# SPDX-License-Identifier: Apache-2.0
"""E2E completion advisor — diagnose failures and ask for what's missing."""

from __future__ import annotations

import re
from typing import Any

from aethos_core.providers.vercel.greenfield_deployment.build_env_criticality import (
    infer_env_integration,
    list_build_critical_env_names,
)
from aethos_core.providers.vercel.diagnostics.build_log_analyzer import analyze_build_logs

_SUPABASE_RX = re.compile(r"supabase", re.I)

_PROVIDER_GUIDANCE: dict[str, dict[str, str]] = {
    "supabase": {
        "label": "Supabase",
        "dashboard": "https://supabase.com/dashboard/project/_/settings/api",
        "action": (
            "Open Supabase → Project Settings → API. Copy **Project URL** and **anon public key** "
            "(and service role if the app needs server actions). Add them to Mission Control → Advanced settings → Credentials "
            "or your local `.env` for solo mode, then redeploy."
        ),
    },
    "stripe": {
        "label": "Stripe",
        "dashboard": "https://dashboard.stripe.com/apikeys",
        "action": "Add Stripe secret/publishable keys to Connections or `.env`, then redeploy.",
    },
    "plaid": {
        "label": "Plaid",
        "dashboard": "https://dashboard.plaid.com/developers/keys",
        "action": "Add Plaid client id/secret to Connections or `.env`, then redeploy.",
    },
    "resend": {
        "label": "Resend",
        "dashboard": "https://resend.com/api-keys",
        "action": "Add Resend API key to Connections or `.env`, then redeploy.",
    },
    "anthropic": {
        "label": "Anthropic",
        "dashboard": "https://console.anthropic.com/settings/keys",
        "action": "Add ANTHROPIC_API_KEY to Connections or `.env`.",
    },
}


def build_e2e_completion_advisory(
    *,
    model,
    params: dict[str, Any],
    env_report: dict[str, Any],
    poll_report: dict[str, Any],
    redeploy_report: dict[str, Any],
    execution_status: str,
) -> dict[str, Any]:
    """Produce human-facing completion plan when E2E did not fully succeed."""
    required_names = _required_env_names(params, env_report)
    framework = str((params.get("target_plan") or {}).get("framework") or params.get("framework") or "")
    build_critical = list_build_critical_env_names(required_names, framework=framework or "nextjs")

    applied = {str(n).upper() for n in (env_report.get("applied_names") or [])}
    failed = [str(n) for n in (env_report.get("failed_names") or [])]
    missing_build = [n for n in build_critical if n.upper() not in applied]

    build_analysis: dict[str, Any] = {}
    log_excerpt: list[str] = []
    root_cause = ""
    if model.provider == "vercel" and execution_status in {
        "failed",
        "polling_failed",
        "verification_failed",
        "env_failed",
    }:
        build_analysis, log_excerpt, root_cause = _analyze_vercel_failure(
            model=model,
            params=params,
            poll_report=poll_report,
            redeploy_report=redeploy_report,
        )

    integration_gaps = _group_missing_by_integration(missing_build or failed)
    questions = _compose_questions(integration_gaps, missing_build, root_cause)
    actions = _compose_actions(integration_gaps, missing_build, env_report, execution_status)
    can_autocomplete = _can_autocomplete_supabase(integration_gaps, missing_build)

    return {
        "root_cause": root_cause or _default_root_cause(execution_status, env_report, poll_report),
        "build_analysis_summary": build_analysis.get("summary") or "",
        "build_error_lines": list(build_analysis.get("error_lines") or log_excerpt)[:6],
        "missing_env_names": missing_build or failed,
        "applied_env_count": len(applied),
        "required_env_count": len(required_names),
        "integration_gaps": integration_gaps,
        "questions_for_you": questions,
        "recommended_actions": actions,
        "can_autocomplete": can_autocomplete,
        "autocomplete_flow": "supabase_env_completion" if can_autocomplete else "",
        "blocked_reason": _blocked_reason(execution_status, missing_build, env_report),
    }


def compose_completion_advisory_report(advisory: dict[str, Any]) -> str:
    lines = [
        "## Why it failed",
        "",
        str(advisory.get("root_cause") or "Deployment did not reach a healthy state."),
        "",
    ]
    for err in advisory.get("build_error_lines") or []:
        lines.append(f"- `{str(err)[:220]}`")
    if advisory.get("build_error_lines"):
        lines.append("")

    missing = list(advisory.get("missing_env_names") or [])
    if missing:
        lines.extend(
            [
                "## Missing setup (env / credentials)",
                "",
                f"- Required for build/runtime: **{len(missing)}** variable(s) still missing from secure store / Connections",
                f"- Applied so far: **{advisory.get('applied_env_count', 0)}** / **{advisory.get('required_env_count', 0)}** detected from repo",
                "",
            ]
        )
        preview = ", ".join(f"`{n}`" for n in missing[:12])
        suffix = f" (+{len(missing) - 12} more)" if len(missing) > 12 else ""
        lines.append(f"- Missing: {preview}{suffix}")
        lines.append("")

    gaps = advisory.get("integration_gaps") or {}
    if gaps:
        lines.extend(["## Services that need credentials", ""])
        for provider, names in gaps.items():
            guide = _PROVIDER_GUIDANCE.get(provider, {})
            label = guide.get("label") or provider.title()
            lines.append(f"### {label}")
            lines.append(f"- Vars: {', '.join(f'`{n}`' for n in names[:8])}")
            if guide.get("dashboard"):
                lines.append(f"- Dashboard: {guide['dashboard']}")
            if guide.get("action"):
                lines.append(f"- **Do this:** {guide['action']}")
            lines.append("")

    questions = list(advisory.get("questions_for_you") or [])
    if questions:
        lines.extend(["## What I need from you", ""])
        for q in questions:
            lines.append(f"- {q}")
        lines.append("")

    actions = list(advisory.get("recommended_actions") or [])
    if actions:
        lines.extend(["## Next steps", ""])
        for i, action in enumerate(actions, 1):
            lines.append(f"{i}. {action}")

    return "\n".join(lines)


def _required_env_names(params: dict[str, Any], env_report: dict[str, Any]) -> list[str]:
    names = list(params.get("env_var_names") or [])
    if names:
        return names
    target = params.get("target_plan") if isinstance(params.get("target_plan"), dict) else {}
    inspection = params.get("inspection") if isinstance(params.get("inspection"), dict) else {}
    return list(
        env_report.get("all_required_names")
        or target.get("required_env_var_names")
        or inspection.get("required_env_var_names")
        or []
    )


def _analyze_vercel_failure(
    *,
    model,
    params: dict[str, Any],
    poll_report: dict[str, Any],
    redeploy_report: dict[str, Any],
) -> tuple[dict[str, Any], list[str], str]:
    from aethos_core.providers.vercel.auth import VercelAuthAdapter
    from aethos_core.providers.vercel.operations.logs_api import fetch_deployment_logs

    credential_id = model.credential_id or str(params.get("credential_id") or "")
    token = VercelAuthAdapter().get_api_token(credential_id) if credential_id else None
    if not token:
        auth = VercelAuthAdapter().resolve_best_auth_method(operation="read_projects")
        credential_id = str(auth.get("credential_id") or "")
        token = VercelAuthAdapter().get_api_token(credential_id) if credential_id else None
    if not token:
        return {}, [], "Vercel build failed — could not fetch logs (token unavailable)."

    deployment_id = str(
        poll_report.get("deployment_id") or redeploy_report.get("deployment_id") or ""
    )
    logs = fetch_deployment_logs(
        token,
        project_name=model.project_name,
        deployment_id=deployment_id or None,
        project_id=str(params.get("project_id") or ""),
    )
    analysis = analyze_build_logs(logs)
    lines = list(analysis.get("error_lines") or [])
    joined = "\n".join(lines + list(logs.get("log_lines") or [])[:20])

    if _SUPABASE_RX.search(joined):
        return analysis, lines, (
            "Vercel build failed during static page generation — the app expects **Supabase** env vars "
            "(URL + anon key) at build time. Without them, Next.js pages like `/settings` and `/dashboard` crash."
        )
    if "npm run build" in joined.lower() or "command failed" in joined.lower():
        return analysis, lines, "Vercel `npm run build` failed — see build log excerpt below."
    if poll_report.get("detail"):
        return analysis, lines, str(poll_report.get("detail"))
    return analysis, lines, "Vercel deployment did not reach ready state."


def _group_missing_by_integration(names: list[str]) -> dict[str, list[str]]:
    grouped: dict[str, list[str]] = {}
    for name in names:
        provider = infer_env_integration(name)
        grouped.setdefault(provider, []).append(name)
    return grouped


def _compose_questions(
    integration_gaps: dict[str, list[str]],
    missing: list[str],
    root_cause: str,
) -> list[str]:
    questions: list[str] = []
    if "supabase" in integration_gaps:
        questions.append(
            "Do you have a Supabase project for this app? If yes, add **Project URL** and **anon key** "
            "via Mission Control → Advanced settings → Credentials (not in chat)."
        )
    if "stripe" in integration_gaps:
        questions.append("Should I use Stripe test keys or live keys for this Vercel deployment?")
    if missing and not integration_gaps:
        questions.append(
            f"Can you add the missing env vars ({', '.join(missing[:5])}{'…' if len(missing) > 5 else ''}) "
            "to Mission Control → Advanced settings → Credentials or your local `.env`?"
        )
    if "Supabase" in root_cause and "supabase" not in integration_gaps:
        questions.append("Which Supabase project should this app use? I need URL + anon key at minimum.")
    if not questions:
        questions.append("Should I retry deploy after you add the missing credentials, or inspect the repo build locally first?")
    return questions


def _compose_actions(
    integration_gaps: dict[str, list[str]],
    missing: list[str],
    env_report: dict[str, Any],
    execution_status: str,
) -> list[str]:
    actions: list[str] = []
    if execution_status == "env_failed" or missing:
        actions.append(
            "Add missing env vars to **Mission Control → Advanced settings → Credentials** (or `.env` for solo mode on your machine)."
        )
    for provider in integration_gaps:
        guide = _PROVIDER_GUIDANCE.get(provider)
        if guide and guide.get("dashboard"):
            actions.append(f"Open {guide['label']} dashboard: {guide['dashboard']}")
    if missing:
        actions.append("Re-run greenfield deploy after env vars are stored — AethOS will apply them and redeploy.")
    if "supabase" in integration_gaps:
        actions.append(
            "Or reply **complete supabase env for <project>** — one approval runs browser → vault → Vercel → redeploy."
        )
    else:
        actions.append("Inspect Vercel build logs in Mission Control → Jobs, fix the repo error, then redeploy.")
    if env_report.get("failed_names"):
        actions.append(
            "Optional: run `inspect vercel env for <project>` to confirm which keys exist (values hidden)."
        )
    return actions


def _default_root_cause(
    execution_status: str,
    env_report: dict[str, Any],
    poll_report: dict[str, Any],
) -> str:
    if execution_status == "env_failed":
        failed = list(env_report.get("failed_names") or [])
        return (
            f"Deploy blocked — {len(failed)} required env var(s) missing from secure store / Connections "
            f"({', '.join(failed[:6])}{'…' if len(failed) > 6 else ''})."
        )
    if execution_status == "polling_failed":
        return str(poll_report.get("detail") or "Deployment polling timed out.")
    return str(poll_report.get("detail") or f"E2E ended with status `{execution_status}`.")


def _blocked_reason(execution_status: str, missing_build: list[str], env_report: dict[str, Any]) -> str:
    if missing_build:
        return "missing_build_critical_env"
    if execution_status == "env_failed":
        return "missing_secure_store_env"
    if execution_status in {"failed", "polling_failed", "verification_failed"}:
        return "deploy_or_build_failed"
    return ""


def _can_autocomplete_supabase(integration_gaps: dict[str, list[str]], missing: list[str]) -> bool:
    if "supabase" not in integration_gaps:
        return False
    try:
        from aethos_core.config import get_settings

        settings = get_settings()
    except Exception:
        return False
    if not settings.provider_e2e_orchestration_enabled:
        return False
    if not settings.mutation_execution_enabled:
        return False
    if not settings.provider_env_var_mutations_enabled:
        return False
    supabase_missing = integration_gaps.get("supabase") or []
    return bool(supabase_missing or missing)

# SPDX-License-Identifier: Apache-2.0
"""Chat routing — Supabase env completion preflight for Vercel deploy targets."""

from __future__ import annotations

from typing import Any

from aethos_core.config import get_settings
from aethos_core.jobs.job_approval_guidance import mutation_approval_surface
from aethos_core.provider_e2e_orchestration.env_completion.supabase_constants import (
    SUPABASE_ENV_COMPLETION_JOB_TYPE,
    SUPABASE_ENV_VAR_NAMES,
    is_supabase_env_completion_request,
    missing_supabase_env_names,
)
from aethos_core.runtime.authority import authority


def route_supabase_env_completion(
    text: str,
    *,
    session_id: str = "default",
) -> tuple[str, str, dict[str, str]] | None:
    if not is_supabase_env_completion_request(text):
        return None

    settings = get_settings()
    if not settings.provider_e2e_orchestration_enabled:
        return _reply(
            "Provider E2E orchestration is disabled. Enable PROVIDER_E2E_ORCHESTRATION_ENABLED to run governed env completion.",
            "supabase_env_completion_disabled",
            stage="orchestration_disabled",
        )

    target = _resolve_target(text, session_id=session_id)
    if not target.get("ok"):
        return _reply(
            str(target.get("detail") or "Could not resolve deploy target from your message."),
            "supabase_env_completion_target_unresolved",
            stage="target_unresolved",
        )

    credential = _resolve_vercel_credential()
    if not credential.get("ok"):
        return _reply(
            str(credential.get("detail") or "Vercel API token required."),
            "supabase_env_completion_missing_credential",
            stage="missing_credential",
        )

    plan = {
        "repo": str(target.get("repo") or ""),
        "project": str(target.get("project_name") or ""),
        "environment": "production",
        "service_name": "",
        "provider": "vercel",
    }
    required = _required_env_names(target)
    missing = missing_supabase_env_names(plan=plan, required_names=required)
    if not missing:
        return _reply(
            f"Supabase env vars for `{plan['project']}` already appear present in secure store. "
            "Reply **redeploy killit** or run Vercel E2E to apply and verify.",
            "supabase_env_completion_already_ready",
            stage="already_ready",
            project=plan["project"],
        )

    steps = [
        "Supervised browser to Supabase → Project Settings → API (you log in; values never enter chat)",
        f"Store `{', '.join(missing)}` in encrypted deployment env vault",
        f"Apply env vars to Vercel project `{plan['project']}`",
        "Production redeploy + poll + verify deployment URL",
    ]

    job_params = {
        "provider": "vercel",
        "flow": "supabase_env_completion",
        "action_type": "supabase_env_completion",
        "session_id": session_id,
        "user_request": text,
        "project_name": plan["project"],
        "referenced_github_repo": plan["repo"],
        "environment": plan["environment"],
        "credential_id": str(credential.get("credential_id") or ""),
        "missing_env_names": missing,
        "env_var_names": list(dict.fromkeys([*missing, *required])),
        "required_env_var_names": required,
        "target_plan": plan,
        "target": {"project_name": plan["project"]},
        "orchestration_steps": steps,
        "browser_extraction_enabled": settings.browser_automation_enabled,
        "execution_status": "awaiting_approval",
        "deploy_action": "redeploy",
    }

    job = authority.create_job(
        title=f"Supabase env completion: {plan['project']}",
        job_type=SUPABASE_ENV_COMPLETION_JOB_TYPE,
        params=job_params,
        source="chat",
        session_id=session_id,
        auto_run=False,
    )

    from aethos_core.jobs.session_approval_target import record_session_approval_target

    record_session_approval_target(
        session_id=session_id,
        job_id=job.id,
        job_type=SUPABASE_ENV_COMPLETION_JOB_TYPE,
        provider="vercel",
        action_type="supabase_env_completion",
        preflight_id=f"supabase-{job.id}",
    )

    body = _compose_preflight_reply(
        job_id=job.id,
        project_name=plan["project"],
        repo=plan["repo"],
        missing=missing,
        steps=steps,
        browser_enabled=settings.browser_automation_enabled,
    )
    return body, "supabase_env_completion_preflight", _meta(
        stage="preflight_created",
        job_id=job.id,
        project=plan["project"],
    )


def _resolve_target(text: str, *, session_id: str) -> dict[str, Any]:
    from aethos_core.deployment_targets.resolver import resolve_deployment_target

    resolved = resolve_deployment_target(text, session_id=session_id)
    if not resolved.get("ok") and not resolved.get("project_name") and not resolved.get("repo"):
        return {"ok": False, "detail": "Name the project (e.g. killit) or repo (e.g. pilotmain/killit)."}
    project = str(resolved.get("project_name") or resolved.get("project") or "").strip()
    repo = str(resolved.get("repo") or resolved.get("referenced_github_repo") or "").strip()
    if not project:
        alias = str(resolved.get("alias") or "").strip()
        project = alias
    if not project and not repo:
        return {"ok": False, "detail": "Could not infer Vercel project from message."}
    return {"ok": True, "project_name": project, "repo": repo, **resolved}


def _required_env_names(target: dict[str, Any]) -> list[str]:
    names = list(target.get("required_env_var_names") or [])
    if names:
        return [str(n).strip().upper() for n in names if str(n).strip()]
    return list(SUPABASE_ENV_VAR_NAMES)


def _resolve_vercel_credential() -> dict[str, Any]:
    from aethos_core.providers.vercel.auth import VercelAuthAdapter

    auth = VercelAuthAdapter().resolve_best_auth_method(operation="read_projects")
    if auth.get("method") != "api_token" or not auth.get("credential_id"):
        return {
            "ok": False,
            "detail": "Add a validated Vercel API token in Mission Control → Advanced settings → Credentials first.",
        }
    return {"ok": True, "credential_id": str(auth.get("credential_id") or "")}


def _compose_preflight_reply(
    *,
    job_id: str,
    project_name: str,
    repo: str,
    missing: list[str],
    steps: list[str],
    browser_enabled: bool,
) -> str:
    lines = [
        "## Supabase env completion (one approval)",
        "",
        f"Target: Vercel **`{project_name}`**" + (f" (`{repo}`)" if repo else ""),
        "",
        "Missing Supabase keys:",
        ", ".join(f"`{n}`" for n in missing),
        "",
        "### Governed chain (single approve)",
    ]
    for i, step in enumerate(steps, 1):
        lines.append(f"{i}. {step}")
    lines.extend(
        [
            "",
            "AethOS will **not** ask for passwords or paste secrets in chat.",
            "",
            f"**Approve once** in {mutation_approval_surface()} (job `{job_id}`), then complete Supabase login in the browser if prompted.",
        ]
    )
    if not browser_enabled:
        lines.extend(
            [
                "",
                "_Browser automation is off — add Supabase URL + anon key via Connections before approving, "
                "or enable BROWSER_AUTOMATION_ENABLED._",
            ]
        )
    return "\n".join(lines)


def _reply(body: str, intent: str, *, stage: str, **extra: str) -> tuple[str, str, dict[str, str]]:
    return body, intent, _meta(stage=stage, **extra)


def _meta(*, stage: str, **extra: str) -> dict[str, str]:
    meta = {
        "route_id": "supabase_env_completion",
        "matched_module": "provider_e2e_orchestration.env_completion.supabase_routing",
        "provider": "vercel",
        "flow": "supabase_env_completion",
        "e2e_stage": stage,
        "readonly": "true",
        "mutation_performed": "false",
        "execution_enabled": "false",
        "presentation_bypass": "true",
    }
    for key, value in extra.items():
        meta[key] = str(value)
    return meta

# SPDX-License-Identifier: Apache-2.0
"""Actionable deployment env resolution reports for blocked deploy outcomes."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from aethos_core.providers.railway.env_value_readiness.env_deployment_filter import (
    filter_greenfield_deployment_env_var_names,
)
from aethos_core.providers.railway.env_value_readiness.env_secure_resolution import (
    build_target_key_for_plan,
    resolve_env_var_from_secure_store,
)
from aethos_core.providers.railway.env_value_readiness.env_value_readiness import (
    credential_center_path,
)

_DEPLOYMENT_ENV_UI_SURFACE = (
    "Mission Control → Advanced settings → Credentials → **Deployment env values** (below provider credentials)"
)

_ENV_PURPOSE_HINTS: dict[str, str] = {
    "ANTHROPIC_API_KEY": "Anthropic LLM API key for chat and agents",
    "OPENAI_API_KEY": "OpenAI API key",
    "WEB_SEARCH_API_KEY": "Web search provider (e.g. Tavily) for research",
    "TAVILY_API_KEY": "Tavily web search API key",
    "RESEND_API_KEY": "Resend email API key",
    "STRIPE_SECRET_KEY": "Stripe secret key for payments",
    "STRIPE_PUBLISHABLE_KEY": "Stripe publishable key (client-side)",
    "SUPABASE_SERVICE_ROLE_KEY": "Supabase service-role key (server-side)",
    "NEXT_PUBLIC_SUPABASE_URL": "Supabase project URL",
    "NEXT_PUBLIC_SUPABASE_ANON_KEY": "Supabase anon/public key",
    "PLAID_CLIENT_ID": "Plaid client id",
    "PLAID_SECRET": "Plaid secret",
    "CRON_SECRET": "Shared secret for cron / scheduled job authentication",
    "DATABASE_URL": "Primary database connection URL",
    "REDIS_URL": "Redis connection URL",
    "GITHUB_TOKEN": "GitHub API token",
    "TELEGRAM_BOT_TOKEN": "Telegram bot token for channel delivery",
    "TRIGGER_WEBHOOK_SECRET": "Trigger.dev webhook signing secret",
    "RAILWAY_API_TOKEN": "Railway API token (provider operations)",
    "VERCEL_TOKEN": "Vercel API token",
}


@dataclass
class DeploymentEnvVarStatus:
    name: str
    purpose: str
    resolved: bool
    source: str = ""
    resolution_source_label: str = ""


@dataclass
class DeploymentEnvAssessment:
    target_key: str
    repo: str
    project: str
    environment: str
    service_name: str
    required: list[DeploymentEnvVarStatus] = field(default_factory=list)
    resolved_names: list[str] = field(default_factory=list)
    missing_names: list[str] = field(default_factory=list)
    stored_names: list[str] = field(default_factory=list)
    ui_surface: str = _DEPLOYMENT_ENV_UI_SURFACE
    credential_center_path: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "target_key": self.target_key,
            "repo": self.repo,
            "project": self.project,
            "environment": self.environment,
            "service_name": self.service_name,
            "required": [
                {
                    "name": row.name,
                    "purpose": row.purpose,
                    "resolved": row.resolved,
                    "source": row.source,
                    "resolution_source_label": row.resolution_source_label,
                }
                for row in self.required
            ],
            "resolved_names": list(self.resolved_names),
            "missing_names": list(self.missing_names),
            "stored_names": list(self.stored_names),
            "ui_surface": self.ui_surface,
            "credential_center_path": self.credential_center_path,
            "missing_count": len(self.missing_names),
            "resolved_count": len(self.resolved_names),
        }


def _purpose_for_name(name: str, hints: dict[str, str]) -> str:
    upper = (name or "").strip().upper()
    if upper in hints and str(hints[upper]).strip():
        return str(hints[upper]).strip()
    if upper in _ENV_PURPOSE_HINTS:
        return _ENV_PURPOSE_HINTS[upper]
    if upper.startswith("NEXT_PUBLIC_"):
        return "Public client-side configuration (safe to expose in browser bundles)"
    if any(token in upper for token in ("_SECRET", "_KEY", "_TOKEN", "_PASSWORD")):
        return "Application secret — store encrypted, never paste in chat"
    return "Required runtime configuration for this deployment target"


def _source_label(source: str) -> str:
    mapping = {
        "credential_center": "Connections (provider credential)",
        "secure_store_reference": "Deployment env values (encrypted store)",
        "local_env_dev_only": "Local environment (dev only)",
    }
    return mapping.get(source or "", source or "unknown")


def assess_deployment_env_for_plan(
    *,
    plan: dict[str, Any],
    env_report: dict[str, Any] | None = None,
) -> DeploymentEnvAssessment:
    plan = dict(plan or {})
    env_report = dict(env_report or {})
    hints = dict(env_report.get("env_var_hints") or plan.get("env_var_hints") or {})
    names = filter_greenfield_deployment_env_var_names(
        list(env_report.get("required_env_var_names") or plan.get("required_env_var_names") or []),
        plan=plan,
    )
    target_key = build_target_key_for_plan(plan)
    from aethos_core.providers.railway.env_value_readiness.deployment_env_store import (
        list_deployment_env_value_names,
    )

    stored_names = list_deployment_env_value_names(target_key=target_key)
    required_rows: list[DeploymentEnvVarStatus] = []
    resolved_names: list[str] = []
    missing_names: list[str] = []

    for raw_name in names:
        upper = str(raw_name).strip().upper()
        if not upper:
            continue
        resolved = resolve_env_var_from_secure_store(upper, plan=plan)
        purpose = _purpose_for_name(upper, hints)
        if resolved.ok:
            resolved_names.append(upper)
            required_rows.append(
                DeploymentEnvVarStatus(
                    name=upper,
                    purpose=purpose,
                    resolved=True,
                    source=resolved.source,
                    resolution_source_label=_source_label(resolved.source),
                )
            )
        else:
            missing_names.append(upper)
            required_rows.append(
                DeploymentEnvVarStatus(
                    name=upper,
                    purpose=purpose,
                    resolved=False,
                    source="",
                    resolution_source_label="",
                )
            )

    return DeploymentEnvAssessment(
        target_key=target_key,
        repo=str(plan.get("repo") or env_report.get("repository") or ""),
        project=str(plan.get("project") or ""),
        environment=str(plan.get("environment") or ""),
        service_name=str(plan.get("service_name") or ""),
        required=required_rows,
        resolved_names=resolved_names,
        missing_names=missing_names,
        stored_names=stored_names,
        credential_center_path=credential_center_path(
            project=str(plan.get("project") or ""),
            environment=str(plan.get("environment") or ""),
            service_name=str(plan.get("service_name") or ""),
        ),
    )


def compose_deployment_env_block_report(assessment: DeploymentEnvAssessment) -> tuple[str, str]:
    """Return (chat_summary, full_markdown) for a blocked deploy due to missing env values."""
    missing = list(assessment.missing_names)
    resolved = list(assessment.resolved_names)
    target_label = (
        f"`{assessment.service_name}`"
        if assessment.service_name
        else f"`{assessment.repo}`"
    )
    from aethos_core.operator_guidance import OperatorStep, compose_operator_guidance

    summary = compose_operator_guidance(
        headline=f"Deploy blocked — {len(missing)} env value(s) only you can provide",
        what_happened=(
            f"I resolved {len(resolved)} of {len(resolved) + len(missing)} required env vars for "
            f"{target_label}; the remaining {len(missing)} are secrets I can't see or generate."
        ),
        aethos_can_do=[
            "Create the project/service, attach the GitHub source, configure all env vars, run the "
            "governed deploy, and verify health — automatically — once the missing values are in.",
        ],
        you_must_do=[
            OperatorStep(
                action=(
                    f"Paste the {len(missing)} missing secret value(s) in the Deployment env values "
                    "section (encrypted; never shown again): "
                    + ", ".join(f"`{n}`" for n in missing[:13])
                ),
                surface="credentials",
                why="only you hold these provider secrets",
            ),
        ],
        safe_next_command="deploy to Railway staging",
    )

    lines = [
        "# Deployment blocked — required env values missing",
        "",
        f"**Target:** {assessment.repo} → {assessment.project} / {assessment.environment} / "
        f"{assessment.service_name or '(new service)'}",
        "",
        f"- **Already resolved ({len(resolved)}):** "
        + (", ".join(f"`{n}`" for n in resolved[:20]) if resolved else "none"),
        f"- **Still need from you ({len(missing)}):** "
        + (", ".join(f"`{n}`" for n in missing[:20]) if missing else "none"),
        "",
        "## Where to add missing values",
        "",
        f"- **Surface:** {assessment.ui_surface}",
        f"- **Path:** {assessment.credential_center_path}",
        f"- **Target key:** `{assessment.target_key}`",
        "",
        "## Required variables",
        "",
    ]
    for row in assessment.required:
        status = "resolved" if row.resolved else "missing"
        src = f" ({row.resolution_source_label})" if row.resolved and row.resolution_source_label else ""
        lines.append(f"- `{row.name}` — {row.purpose} — **{status}**{src}")

    lines.extend(
        [
            "",
            "## Next step",
            "",
            "1. Open **Mission Control → Advanced settings → Credentials → Deployment env values**.",
            "2. Select this deployment target and paste the missing secret values (encrypted; never shown again).",
            "3. Re-run the same deploy request in chat (e.g. deploy to Railway staging).",
            "",
            "Provider credentials in **Connections** auto-fill matching names (e.g. `ANTHROPIC_API_KEY` from Anthropic).",
        ]
    )
    return summary, "\n".join(lines)

# SPDX-License-Identifier: Apache-2.0
"""Railway deployment plan human review and confirmation before mutation."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from aethos_core.providers.railway.deployment_plan.deployment_plan_artifact import format_plan_risk_line
from aethos_core.providers.railway.deployment_plan.env_var_summary import (
    categorize_env_var_names,
    format_env_var_section_lines,
)
from aethos_core.providers.railway.deployment_plan.plan_readiness_gate import assess_mutation_readiness_gate


def is_plan_review_confirmed(plan: dict[str, Any]) -> bool:
    return bool(plan.get("review_confirmed"))


def plan_ready_for_review(plan: dict[str, Any]) -> bool:
    """Technical fields populated enough to present for human confirmation."""
    gate = assess_mutation_readiness_gate(plan)
    return bool(gate.get("mutation_ready"))


def _format_env_summary(plan: dict[str, Any]) -> list[str]:
    names = list(plan.get("required_env_var_names") or [])
    return format_env_var_section_lines(names, categorized=plan.get("env_var_summary") or None)


def compose_plan_review_request(plan: dict[str, Any]) -> str:
    project = str(plan.get("project") or "—")
    environment = str(plan.get("environment") or "—")
    service_name = str(plan.get("service_name") or "—")
    start_cmd = str(plan.get("start_command") or "unknown")
    risk = format_plan_risk_line(
        environment=str(plan.get("environment") or ""),
        risk_tier=str(plan.get("risk_tier") or ""),
    )

    lines = [
        "# Railway Deployment Plan — Review Required",
        "",
        "Before any new Railway service mutation, confirm these high-risk assumptions:",
        "",
        f"- **Service name:** `{service_name}`",
        f"- **Project / environment:** `{project}` / `{environment}`",
        f"- **Start command:** `{start_cmd}`",
        "",
        "**Required env var names (no values):**",
    ]
    env_lines = _format_env_summary(plan)
    for line in env_lines[1:]:
        if line.startswith("Required env vars:"):
            continue
        lines.append(line)
    lines.extend(
        [
            "",
            f"- **Production risk:** {risk}",
            "",
            "If this looks correct, reply:",
            "`confirm railway deployment plan`",
            "",
            "To see the full governed plan again:",
            "`show railway deployment plan`",
            "",
            "No service has been created.",
            "No mutation has been performed.",
        ]
    )
    return "\n".join(lines)


def apply_plan_review_confirmation(plan: dict[str, Any]) -> dict[str, Any]:
    updated = dict(plan)
    updated["review_confirmed"] = True
    updated["review_confirmed_at"] = datetime.now(UTC).isoformat()
    updated["stage"] = "review_confirmed"
    return updated


def compose_plan_review_confirmed(plan: dict[str, Any]) -> str:
    project = str(plan.get("project") or "—")
    environment = str(plan.get("environment") or "—")
    service_name = str(plan.get("service_name") or "—")
    start_cmd = str(plan.get("start_command") or "unknown")
    risk = format_plan_risk_line(
        environment=str(plan.get("environment") or ""),
        risk_tier=str(plan.get("risk_tier") or ""),
    )
    gate = assess_mutation_readiness_gate(plan)

    lines = [
        "# Railway Deployment Plan — Review Confirmed",
        "",
        "You confirmed the governed assumptions for this new-service deployment:",
        "",
        f"- Service name: `{service_name}`",
        f"- Project / environment: `{project}` / `{environment}`",
        f"- Start command: `{start_cmd}`",
        f"- Production risk: {risk}",
        "",
        "Required env var names were acknowledged (names only, no secrets in chat).",
        "",
        "Plan review:",
        "- review_confirmed: true",
        "",
        "Readiness gate:",
        f"- mutation_ready: {'true' if gate.get('mutation_ready') else 'false'}",
        "- mutation execution: **not enabled yet** in this runtime",
        "",
        "No service has been created.",
        "No mutation has been performed.",
    ]
    return "\n".join(lines)


def format_review_status_lines(plan: dict[str, Any]) -> list[str]:
    confirmed = is_plan_review_confirmed(plan)
    lines = [
        "Plan review:",
        f"- review_confirmed: {'true' if confirmed else 'false'}",
    ]
    if not confirmed and plan_ready_for_review(plan):
        lines.append("- action: `review railway deployment plan` then `confirm railway deployment plan`")
    return lines

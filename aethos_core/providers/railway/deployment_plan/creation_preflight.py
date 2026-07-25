# SPDX-License-Identifier: Apache-2.0
"""Governed Railway new-service creation preflight artifact — approval only, no execution."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime
from typing import Any

from aethos_core.providers.railway.deployment_plan.deployment_plan_artifact import format_plan_risk_line
from aethos_core.providers.railway.deployment_plan.env_var_summary import format_env_var_section_lines
from aethos_core.providers.railway.deployment_plan.plan_readiness_gate import assess_mutation_readiness_gate
from aethos_core.providers.railway.deployment_plan.plan_review import is_plan_review_confirmed


def plan_eligible_for_creation_preflight(plan: dict[str, Any]) -> tuple[bool, list[str]]:
    blockers: list[str] = []
    if not plan or not plan.get("repo"):
        blockers.append("saved_deployment_plan")
    if not is_plan_review_confirmed(plan or {}):
        blockers.append("review_confirmed")
    gate = assess_mutation_readiness_gate(plan or {})
    if not gate.get("mutation_ready"):
        blockers.extend(list(gate.get("missing") or []))
    return not blockers, blockers


def build_creation_preflight_from_plan(plan: dict[str, Any]) -> dict[str, Any]:
    env_names = list(plan.get("required_env_var_names") or [])
    risk = format_plan_risk_line(
        environment=str(plan.get("environment") or ""),
        risk_tier=str(plan.get("risk_tier") or ""),
    )
    return {
        "preflight_id": f"rpref-{uuid.uuid4().hex[:12]}",
        "plan_id": str(plan.get("plan_id") or ""),
        "repo": str(plan.get("repo") or ""),
        "plan_snapshot": dict(plan),
        "stage": "preflight_draft",
        "preflight_approved": False,
        "execution_enabled": False,
        "mutation_performed": False,
        "risk_line": risk,
        "unset_env_var_names": list(env_names),
        "created_at": datetime.now(UTC).isoformat(),
    }


def apply_preflight_approval(preflight: dict[str, Any]) -> dict[str, Any]:
    updated = dict(preflight)
    updated["preflight_approved"] = True
    updated["approved_at"] = datetime.now(UTC).isoformat()
    updated["stage"] = "preflight_approved"
    return updated


def compose_creation_preflight_artifact(preflight: dict[str, Any]) -> str:
    plan = dict(preflight.get("plan_snapshot") or {})
    project = str(plan.get("project") or "—")
    environment = str(plan.get("environment") or "—")
    service_name = str(plan.get("service_name") or "—")
    repo = str(plan.get("repo") or "—")
    branch = str(plan.get("branch") or "main")
    build_cmd = str(plan.get("build_command") or "unknown")
    start_cmd = str(plan.get("start_command") or "unknown")
    runtime = str(plan.get("runtime") or "unknown")
    health = str(plan.get("health_check_path") or "unknown")
    risk = str(preflight.get("risk_line") or format_plan_risk_line(environment=environment))
    approved = bool(preflight.get("preflight_approved"))
    env_names = list(preflight.get("unset_env_var_names") or [])

    env_section = format_env_var_section_lines(
        env_names,
        categorized=plan.get("env_var_summary") or None,
    )
    env_body: list[str] = []
    for line in env_section:
        if line.startswith("Required env vars:"):
            continue
        env_body.append(line)

    from aethos_core.providers.railway.env_value_readiness.env_value_readiness import (
        format_env_value_readiness_lines,
    )
    from aethos_core.providers.railway.env_value_readiness.env_value_readiness import (
        get_or_assess_env_value_readiness,
    )

    env_state = get_or_assess_env_value_readiness(plan=plan, session_id=str(preflight.get("session_id") or "default"))

    lines = [
        "# Railway New Service Creation Preflight",
        "",
        f"Preflight ID: `{preflight.get('preflight_id')}`",
        "",
        "## Target (from confirmed deployment plan)",
        f"- Service name: `{service_name}`",
        f"- Project / environment: `{project}` / `{environment}`",
        f"- Source: `{repo}` @ `{branch}`",
        f"- Runtime: {runtime}",
        f"- Build: `{build_cmd}`",
        f"- Start: `{start_cmd}`",
        f"- Health check: `{health}`",
        "",
        "## Blast radius",
        "- **Creates a new Railway service** (greenfield — not restart/redeploy of an existing service)",
        f"- **Environment:** `{environment}` — {risk}",
        f"- **Connects GitHub repo** `{repo}` for deploy-from-source",
        "- **First deploy** will run build + start commands on Railway infrastructure",
        "- **Production-impacting** if environment is production",
        "",
        "## Service creation diff",
        "```diff",
        f"+ service: {service_name}  (new)",
        f"+ project: {project}",
        f"+ environment: {environment}",
        f"+ github_source: {repo}@{branch}",
        f"+ build_command: {build_cmd}",
        f"+ start_command: {start_cmd}",
        f"+ health_check_path: {health}",
        "```",
        "",
        "## Required env vars (still unset on Railway)",
        "These names are required for the app; **no values are set** until after service creation:",
    ]
    lines.extend(env_body if env_body else ["- (none detected in plan)"])
    lines.extend(format_env_value_readiness_lines(env_state))
    lines.extend(
        [
            "",
            "## Rollback",
            "- Remove the created Railway service if creation proceeds",
            "- Disable auto-deploy on the new service",
            "- Disconnect GitHub source binding if created",
            "- Revert any service-scoped env var writes",
            "",
            "## Approval",
            f"- preflight_approved: {'true' if approved else 'false'}",
            "- explicit_approval_required: **true**",
            "- service_creation_execution: **not enabled yet** in this runtime",
            "",
        ]
    )
    if not approved:
        lines.extend(
            [
                "To approve this preflight (still no Railway mutation):",
                "`approve railway service creation preflight`",
                "",
            ]
        )
    lines.extend(
        [
            "No Railway service has been created.",
            "No mutation has been performed.",
        ]
    )
    return "\n".join(lines)

# SPDX-License-Identifier: Apache-2.0
"""Complete Railway deployment plans using readonly GitHub repo inspection."""

from __future__ import annotations

from typing import Any

from aethos_core.providers.railway.deployment_plan.deployment_plan_artifact import (
    infer_service_name_from_repo,
    normalize_plan_for_artifact,
    render_railway_deployment_plan_artifact,
)
from aethos_core.providers.railway.deployment_plan.env_var_summary import (
    categorize_env_var_names,
    format_env_var_names_inline,
)
from aethos_core.providers.railway.deployment_plan.plan_readiness_gate import (
    assess_mutation_readiness_gate,
    format_readiness_gate_lines,
)
from aethos_core.providers.railway.deployment_plan.repo_inspection import (
    inspect_github_repo_for_deployment,
    is_health_probe_command,
)


def assess_plan_completion(plan: dict[str, Any]) -> tuple[str, list[str]]:
    """Return plan status complete|incomplete and human-readable missing labels."""
    gate = assess_mutation_readiness_gate(plan)
    status = "complete" if gate["mutation_ready"] else "incomplete"
    return status, list(gate.get("missing_labels") or [])


def merge_inspection_into_plan(
    plan: dict[str, Any],
    *,
    inspection: dict[str, Any],
) -> dict[str, Any]:
    """Update saved plan fields from readonly repo inspection."""
    updated = dict(plan)
    if not inspection.get("ok"):
        updated["repo_inspection_ok"] = False
        updated["repo_inspection_error"] = str(inspection.get("error") or "inspection failed")
        updated["deployment_readiness"] = "incomplete"
        return updated

    fields = dict(inspection.get("fields") or {})
    updated["repo_inspection_ok"] = True
    updated["repo_inspection"] = {
        "repository": inspection.get("repository"),
        "branch": inspection.get("branch"),
        "root_files": list(inspection.get("root_files") or [])[:40],
        "files_inspected": list(inspection.get("files_inspected") or []),
        "manifests_present": fields.get("manifests_present") or [],
    }
    updated["runtime"] = str(fields.get("runtime") or "unknown")
    updated["build_command"] = str(fields.get("build_command") or "unknown")
    start_cmd = str(fields.get("start_command") or "unknown")
    if is_health_probe_command(start_cmd):
        start_cmd = "unknown"
    updated["start_command"] = start_cmd
    updated["health_check_path"] = str(fields.get("health_check_path") or "unknown")
    env_names = list(fields.get("required_env_var_names") or [])
    updated["required_env_var_names"] = env_names
    updated["env_var_summary"] = categorize_env_var_names(env_names)
    updated["service_name_confidence"] = str(fields.get("service_name_confidence") or "low")

    pkg_name = str(fields.get("package_name") or "").strip()
    if pkg_name and str(updated.get("service_name_confidence")) == "high":
        updated["service_name"] = pkg_name
    elif not updated.get("service_name"):
        updated["service_name"] = infer_service_name_from_repo(str(updated.get("repo") or ""))

    gate = assess_mutation_readiness_gate(updated)
    updated["mutation_ready"] = bool(gate["mutation_ready"])
    updated["readiness_gate_missing"] = list(gate.get("missing") or [])
    status, missing = assess_plan_completion(updated)
    updated["deployment_readiness"] = status
    updated["missing_fields"] = missing
    updated["stage"] = "plan_complete" if gate["mutation_ready"] else "plan_inspected"
    updated["review_confirmed"] = bool(plan.get("review_confirmed"))
    return updated


def render_plan_completion_artifact(
    plan: dict[str, Any],
    *,
    inspection: dict[str, Any],
) -> str:
    fields = dict(inspection.get("fields") or {}) if inspection.get("ok") else {}
    env_names = list(fields.get("required_env_var_names") or plan.get("required_env_var_names") or [])
    env_summary = plan.get("env_var_summary") or categorize_env_var_names(env_names)
    env_display = format_env_var_names_inline(env_names, categorized=env_summary)
    status = str(plan.get("deployment_readiness") or "incomplete")
    missing = list(plan.get("missing_fields") or [])

    lines = [
        "# Railway Deployment Plan Completion",
        "",
        "Repo inspection:",
        f"- Runtime: {fields.get('runtime') or plan.get('runtime') or 'unknown'}",
        f"- Build command: {fields.get('build_command') or plan.get('build_command') or 'unknown'}",
        f"- Start command: {fields.get('start_command') or plan.get('start_command') or 'unknown'}",
        f"- Env var names: {env_display}",
        f"- Health check path: {fields.get('health_check_path') or plan.get('health_check_path') or 'unknown'}",
        f"- Service name confidence: {fields.get('service_name_confidence') or plan.get('service_name_confidence') or 'low'}",
        "",
        "Plan status:",
        f"- {status}",
        "",
    ]
    lines.extend(format_readiness_gate_lines(plan))
    lines.append("")
    if missing:
        lines.append("Missing:")
        for item in missing:
            lines.append(f"- {item}")
    else:
        lines.append("Missing:")
        lines.append("- (none)")
    from aethos_core.providers.railway.deployment_plan.plan_review import format_review_status_lines

    lines.extend(format_review_status_lines(plan))
    lines.extend(
        [
            "",
            "Next: `review railway deployment plan` then `confirm railway deployment plan`",
            "",
            "No secrets requested.",
            "No service has been created.",
            "No env vars written.",
            "No mutation has been performed.",
        ]
    )
    return "\n".join(lines)


def complete_railway_deployment_plan(
    plan: dict[str, Any],
    *,
    checks: dict[str, Any] | None = None,
) -> tuple[str, dict[str, Any], dict[str, Any]]:
    """Inspect repo, merge into plan, return completion summary + updated plan context."""
    repo = str(plan.get("repo") or "").strip()
    branch = str(plan.get("branch") or "main")
    inspection = inspect_github_repo_for_deployment(repository=repo, branch=branch)
    updated = merge_inspection_into_plan(plan, inspection=inspection)
    completion = render_plan_completion_artifact(updated, inspection=inspection)
    full_plan = render_railway_deployment_plan_artifact(
        normalize_plan_for_artifact(updated),
        checks=checks,
        include_readiness_line=False,
    )
    body = f"{completion}\n\n---\n\n{full_plan}"
    return body, updated, inspection

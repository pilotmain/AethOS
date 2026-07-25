# SPDX-License-Identifier: Apache-2.0
"""Compose Railway new-service deployment plan artifacts."""

from __future__ import annotations

import re
from typing import Any

from aethos_core.operations.mutations.risk import MutationRiskTier

_PROJECT_ENV_RX = re.compile(
    r"\b(?:in|on)\s+([a-z0-9][a-z0-9._-]*)\s*/\s*([a-z0-9][a-z0-9._-]*)\b",
    re.I,
)
_SERVICE_NAME_RX = re.compile(
    r"\bservice\s+(?:name\s+)?[`'\"]?([a-z0-9][a-z0-9._-]+)[`'\"]?\b",
    re.I,
)
_BRANCH_RX = re.compile(r"\bbranch\s+[`'\"]?([a-z0-9][a-z0-9._/._-]+)[`'\"]?\b", re.I)


def infer_service_name_from_repo(repo: str) -> str:
    base = (repo.split("/")[-1] if "/" in repo else repo).strip().lower()
    if not base:
        return "new-service"
    if base.endswith("-api"):
        return base
    if base in {"aethos", "pilotos", "pilotos-api"}:
        return "aethos-api" if base == "aethos" else base
    return f"{base}-api"


def classify_plan_risk(*, environment: str | None) -> MutationRiskTier:
    env = (environment or "").strip().lower()
    if env in {"production", "prod"}:
        return MutationRiskTier.T3_PRODUCTION
    if env in {"staging", "stage", "dev", "development", "preview"}:
        return MutationRiskTier.T2_LOW_RISK
    return MutationRiskTier.T3_PRODUCTION


def parse_plan_fields_from_text(text: str, *, default_repo: str = "") -> dict[str, str | None]:
    raw = (text or "").strip()
    from aethos_core.providers.railway.deployment_readiness.deployment_readiness_checks import (
        extract_github_repo_target,
    )

    repo = extract_github_repo_target(raw) or default_repo or None
    branch = None
    branch_match = _BRANCH_RX.search(raw)
    if branch_match:
        branch = branch_match.group(1).strip()
    project = None
    environment = None
    pe = _PROJECT_ENV_RX.search(raw)
    if pe:
        project = pe.group(1).strip()
        environment = pe.group(2).strip()
    service_name = None
    sn = _SERVICE_NAME_RX.search(raw)
    if sn:
        service_name = sn.group(1).strip()
    return {
        "repo": repo,
        "branch": branch or "main",
        "project": project,
        "environment": environment,
        "service_name": service_name,
    }


def list_railway_project_environment_options() -> list[dict[str, str]]:
    options: list[dict[str, str]] = []
    try:
        from aethos_core.providers.railway.discovery import discover_railway_inventory

        inventory = discover_railway_inventory()
        for project in inventory.projects[:12]:
            for env in project.environments[:6]:
                options.append(
                    {
                        "project": project.name,
                        "environment": env.name,
                        "path": f"{project.name} / {env.name}",
                    }
                )
    except Exception:
        pass
    return options


def compose_target_clarification(
    *,
    repo: str,
    options: list[dict[str, str]],
    missing: tuple[str, ...],
) -> str:
    lines = [
        "I can draft the Railway new-service deployment plan, but I need a target workspace first.",
        "",
        f"**Source repo:** `{repo}`",
        "",
        "Which Railway project/environment should this new service use?",
    ]
    if options:
        lines.append("")
        lines.append("**Options:**")
        for idx, row in enumerate(options[:8], start=1):
            lines.append(f"{idx}. `{row.get('path')}`")
    else:
        lines.append("")
        lines.append(
            "I could not list Railway projects from inventory. "
            "Reply with `project / environment`, for example `pilotos / production`."
        )
    if "service_name" in missing:
        lines.extend(
            [
                "",
                "Also specify the **service name** (for example `aethos-api`), or say **use default** "
                f"to use `{infer_service_name_from_repo(repo)}`.",
            ]
        )
    lines.extend(["", "No service has been created. No mutation has been performed."])
    return "\n".join(lines)


def format_plan_risk_line(*, environment: str | None, risk_tier: str | None = None) -> str:
    tier = (risk_tier or classify_plan_risk(environment=environment).value).strip()
    env = (environment or "").strip().lower()
    if tier == MutationRiskTier.T2_LOW_RISK.value or env in {"staging", "stage", "dev", "development", "preview"}:
        return "T2 staging/dev"
    return "T3 production impacting"


def normalize_plan_for_artifact(plan: dict[str, Any]) -> dict[str, Any]:
    """Fill defaults so show/create always render the full governed artifact."""
    repo = str(plan.get("repo") or "").strip()
    environment = str(plan.get("environment") or "").strip() or None
    normalized = dict(plan)
    normalized["repo"] = repo or "owner/repo"
    normalized["branch"] = str(plan.get("branch") or "main")
    normalized["project"] = str(plan.get("project") or "").strip() or None
    normalized["environment"] = environment
    normalized["service_name"] = str(plan.get("service_name") or "").strip() or infer_service_name_from_repo(
        normalized["repo"]
    )
    normalized["build_command"] = str(plan.get("build_command") or "unknown / inferred")
    normalized["start_command"] = str(plan.get("start_command") or "unknown / inferred")
    normalized["runtime"] = str(plan.get("runtime") or "unknown / inferred")
    normalized["health_check_path"] = str(plan.get("health_check_path") or "unknown")
    env_names = plan.get("required_env_var_names")
    normalized["required_env_var_names"] = list(env_names) if isinstance(env_names, list) else []
    summary = plan.get("env_var_summary")
    normalized["env_var_summary"] = summary if isinstance(summary, dict) else {}
    normalized["mutation_ready"] = bool(plan.get("mutation_ready")) if "mutation_ready" in plan else False
    normalized["readiness_gate_missing"] = list(plan.get("readiness_gate_missing") or [])
    normalized["risk_tier"] = str(
        plan.get("risk_tier") or classify_plan_risk(environment=environment).value
    )
    normalized.setdefault("mutation_ready", False)
    normalized.setdefault("stage", plan.get("stage") or "plan_draft")
    normalized.setdefault("deployment_readiness", plan.get("deployment_readiness") or "incomplete")
    normalized["review_confirmed"] = bool(plan.get("review_confirmed"))
    return normalized


def compose_readiness_status_line(checks: dict[str, Any] | None) -> str:
    if not checks:
        return ""
    from aethos_core.providers.railway.deployment_readiness.deployment_readiness_plan import (
        readonly_checks_passed,
    )

    if readonly_checks_passed(checks):
        if checks.get("mutation_ready"):
            return "Readiness: all readonly checks passed; mutation path available."
        return "Readiness: all readonly checks passed (no mutation performed yet)."
    return "Readiness: blocked — run `run railway deployment readiness for <owner/repo>` first."


def compose_plan_reply(
    plan: dict[str, Any],
    *,
    checks: dict[str, Any] | None = None,
    include_readiness_line: bool = True,
) -> str:
    """Full deployment plan artifact; optional one-line readiness status above the plan."""
    return render_railway_deployment_plan_artifact(
        plan,
        checks=checks,
        include_readiness_line=include_readiness_line,
    )


def render_railway_deployment_plan_artifact(
    plan_context: dict[str, Any],
    *,
    checks: dict[str, Any] | None = None,
    include_readiness_line: bool = True,
    session_id: str = "default",
) -> str:
    """Single source for create/show Railway new-service deployment plan rendering."""
    normalized = normalize_plan_for_artifact(plan_context)
    artifact = compose_deployment_plan_artifact(normalized, session_id=session_id)
    if not include_readiness_line:
        return artifact
    status = compose_readiness_status_line(checks)
    if not status:
        return artifact
    return f"{status}\n\n{artifact}"


def compose_deployment_plan_artifact(plan: dict[str, Any], *, session_id: str = "default") -> str:
    normalized = normalize_plan_for_artifact(plan)
    repo = str(normalized["repo"])
    branch = str(normalized["branch"])
    project = str(normalized.get("project") or "— (confirm)")
    environment = str(normalized.get("environment") or "— (confirm)")
    service_name = str(normalized["service_name"])
    risk_line = format_plan_risk_line(
        environment=str(normalized.get("environment") or ""),
        risk_tier=str(normalized.get("risk_tier") or ""),
    )
    build_cmd = str(normalized["build_command"])
    start_cmd = str(normalized["start_command"])
    runtime = str(normalized["runtime"])
    health_path = str(normalized.get("health_check_path") or "unknown")
    env_names = list(normalized.get("required_env_var_names") or [])
    readiness = str(normalized.get("deployment_readiness") or "incomplete")
    from aethos_core.providers.railway.deployment_plan.env_var_summary import format_env_var_section_lines
    from aethos_core.providers.railway.deployment_plan.plan_readiness_gate import format_readiness_gate_lines
    from aethos_core.providers.railway.deployment_plan.plan_review import format_review_status_lines

    env_lines = format_env_var_section_lines(
        env_names,
        categorized=normalized.get("env_var_summary") or None,
    )
    from aethos_core.providers.railway.env_value_readiness.env_value_readiness import (
        format_env_value_readiness_lines,
        get_or_assess_env_value_readiness,
    )

    env_value_lines = format_env_value_readiness_lines(
        get_or_assess_env_value_readiness(plan=normalized, session_id=session_id)
    )
    gate_lines = format_readiness_gate_lines(normalized)
    review_lines = format_review_status_lines(normalized)

    return "\n".join(
        [
            "# Railway New Service Deployment Plan",
            "",
            "Target source:",
            f"- Repo: {repo}",
            f"- Branch: {branch}",
            "",
            "Railway target:",
            f"- Project: {project}",
            f"- Environment: {environment}",
            f"- Service name: {service_name}",
            "",
            "Build/runtime:",
            f"- Build command: {build_cmd}",
            f"- Start command: {start_cmd}",
            f"- Runtime: {runtime}",
            f"- Health check path: {health_path}",
            "",
            *env_lines,
            "",
            *env_value_lines,
            "",
            "Deployment readiness:",
            f"- {readiness}",
            "",
            *gate_lines,
            "",
            *review_lines,
            "",
            "Governed execution plan:",
            "1. Create Railway service",
            "2. Connect GitHub repo/source",
            "3. Configure env vars",
            "4. Trigger first deploy",
            "5. Watch build/deploy logs",
            "6. Verify health/domain",
            "7. Persist deployment lifecycle",
            "",
            "Risk:",
            f"- {risk_line}",
            "",
            "Rollback:",
            "- Remove created service or disable deployment",
            "- Revert env/source binding if created",
            "",
            "Verification:",
            "- inspect deployment logs",
            "- check runtime health",
            "- capture service URL/domain if assigned",
            "",
            "No service has been created.",
            "No mutation has been performed.",
        ]
    )

# SPDX-License-Identifier: Apache-2.0
"""Readonly dry-run checks for Railway greenfield service creation execution."""

from __future__ import annotations

from typing import Any

from aethos_core.providers.railway.deployment_plan.plan_readiness_gate import assess_mutation_readiness_gate
from aethos_core.providers.railway.deployment_plan.repo_inspection import is_health_probe_command
from aethos_core.providers.railway.deployment_readiness.deployment_readiness_checks import (
    _CANONICAL_CREDENTIAL_SOURCE,
    _probe_github_binding,
    _resolve_railway_token_canonical,
)


def _norm(value: str) -> str:
    return (value or "").strip().lower()


def _check_row(
    check: str,
    status: str,
    *,
    details: str = "",
    **extra: Any,
) -> dict[str, Any]:
    row: dict[str, Any] = {"check": check, "status": status, "details": details}
    row.update(extra)
    return row


def suggest_service_name_alternatives(service_name: str) -> list[str]:
    base = (service_name or "new-service").strip()
    return [f"{base}-2", f"{base}-new"]


def _find_project_environment(
    inventory: Any,
    *,
    project_name: str,
    environment_name: str,
) -> tuple[dict[str, Any] | None, dict[str, Any] | None, str]:
    if getattr(inventory, "error", None):
        return None, None, str(inventory.error)
    for project in getattr(inventory, "projects", []) or []:
        if _norm(project.name) != _norm(project_name):
            continue
        for environment in project.environments or []:
            if _norm(environment.name) == _norm(environment_name):
                return (
                    {"id": project.id, "name": project.name},
                    {"id": environment.id, "name": environment.name},
                    "",
                )
        return (
            {"id": project.id, "name": project.name},
            None,
            f"Environment `{environment_name}` not found in project `{project_name}`.",
        )
    return None, None, f"Project `{project_name}` not found in Railway inventory."


def _probe_live_railway_inventory(
    *,
    project_name: str,
    environment_name: str,
) -> dict[str, Any]:
    from aethos_core.providers.railway.service_creation_simulator.simulator_lifecycle_snapshots import (
        classify_inventory_probe_failure,
    )

    try:
        from aethos_core.providers.railway.discovery import discover_railway_inventory

        inventory = discover_railway_inventory()
    except Exception as exc:
        err = str(exc)
        return {
            "pass": False,
            "error": err,
            "reason": classify_inventory_probe_failure(err),
            "project": None,
            "environment": None,
        }

    if getattr(inventory, "error", None):
        err = str(inventory.error)
        return {
            "pass": False,
            "error": err,
            "reason": classify_inventory_probe_failure(err),
            "project": None,
            "environment": None,
        }

    proj, env, err = _find_project_environment(
        inventory,
        project_name=project_name,
        environment_name=environment_name,
    )
    if proj and env:
        return {
            "pass": True,
            "error": "",
            "reason": "",
            "project": proj,
            "environment": env,
        }
    return {
        "pass": False,
        "error": err or f"Project `{project_name}` / environment `{environment_name}` not found in live inventory.",
        "reason": classify_inventory_probe_failure(err or ""),
        "project": proj,
        "environment": env,
    }


def check_railway_project_environment(
    *,
    plan: dict[str, Any],
    session_id: str = "default",
) -> dict[str, Any]:
    from aethos_core.providers.railway.service_creation_simulator.simulator_lifecycle_snapshots import (
        inventory_probe_diagnostic,
        lifecycle_supports_project_environment,
    )

    project = str(plan.get("project") or "")
    environment = str(plan.get("environment") or "")
    if not project or not environment:
        return _check_row(
            "railway_project_environment",
            "fail",
            project=project,
            environment=environment,
            details="Project and environment must be set on the deployment plan.",
        )

    live = _probe_live_railway_inventory(project_name=project, environment_name=environment)
    snapshot_ok, snapshot_source, _snapshot_checks = lifecycle_supports_project_environment(
        plan=plan,
        session_id=session_id,
    )
    probe = inventory_probe_diagnostic(live=live)

    if live.get("pass"):
        proj = dict(live.get("project") or {})
        env = dict(live.get("environment") or {})
        row = _check_row(
            "railway_project_environment",
            "pass",
            project=project,
            environment=environment,
            project_id=proj.get("id"),
            environment_id=env.get("id"),
            resolution_source="live_inventory_probe",
            details=f"Resolved project `{project}` and environment `{environment}`.",
        )
        if probe:
            row["inventory_probe"] = probe
        return row

    if snapshot_ok:
        row = _check_row(
            "railway_project_environment",
            "pass",
            project=project,
            environment=environment,
            resolution_source=snapshot_source,
            details=(
                f"Resolved project `{project}` and environment `{environment}` from "
                f"{snapshot_source}."
            ),
        )
        if probe:
            row["inventory_probe"] = probe
        return row

    status = "unknown" if not str(live.get("error") or "").strip() else "fail"
    row = _check_row(
        "railway_project_environment",
        status,
        project=project,
        environment=environment,
        details=str(live.get("error") or "Project/environment could not be resolved."),
    )
    if probe:
        row["inventory_probe"] = probe
    return row


def check_service_name_availability(
    *,
    plan: dict[str, Any],
    project_environment_check: dict[str, Any],
) -> dict[str, Any]:
    service_name = str(plan.get("service_name") or "")
    project = str(plan.get("project") or "")
    environment = str(plan.get("environment") or "")
    if project_environment_check.get("status") != "pass":
        return _check_row(
            "service_name_availability",
            "unknown",
            service_name=service_name,
            project=project,
            environment=environment,
            details="Skipped — project/environment could not be resolved.",
        )

    if project_environment_check.get("resolution_source") == "deployment lifecycle readiness snapshot":
        live = _probe_live_railway_inventory(project_name=project, environment_name=environment)
        if not live.get("pass"):
            return _check_row(
                "service_name_availability",
                "unknown",
                service_name=service_name,
                project=project,
                environment=environment,
                details=(
                    "Live inventory probe unavailable; service name conflict check skipped "
                    f"(plan target: {project} / {environment})."
                ),
            )

    try:
        from aethos_core.providers.railway.discovery import discover_railway_inventory

        inventory = discover_railway_inventory()
    except Exception as exc:
        return _check_row(
            "service_name_availability",
            "unknown",
            service_name=service_name,
            details=f"Inventory unavailable: {exc}",
        )

    for proj in inventory.projects:
        if _norm(proj.name) != _norm(project):
            continue
        for env in proj.environments:
            if _norm(env.name) != _norm(environment):
                continue
            existing = [_norm(svc.name) for svc in env.services]
            if _norm(service_name) in existing:
                alts = suggest_service_name_alternatives(service_name)
                return _check_row(
                    "service_name_availability",
                    "fail",
                    service_name=service_name,
                    project=project,
                    environment=environment,
                    suggested_alternatives=alts,
                    details=(
                        f"A service named `{service_name}` already exists in {project} / {environment}."
                    ),
                )
            return _check_row(
                "service_name_availability",
                "pass",
                service_name=service_name,
                project=project,
                environment=environment,
                details=(
                    f"Target service name `{service_name}` is not currently present in {project} / {environment}."
                ),
            )
    return _check_row(
        "service_name_availability",
        "unknown",
        service_name=service_name,
        details="Could not locate project/environment services in inventory.",
    )


def check_github_source_binding(*, plan: dict[str, Any]) -> dict[str, Any]:
    repo = str(plan.get("repo") or "")
    branch = str(plan.get("branch") or "main")
    if not repo:
        return _check_row(
            "github_source_binding",
            "fail",
            repository=repo,
            branch=branch,
            details="Deployment plan is missing GitHub repository target.",
        )

    binding = _probe_github_binding(referenced_repo=repo)
    if not binding.get("github_credential_ok"):
        return _check_row(
            "github_source_binding",
            "fail",
            repository=repo,
            branch=branch,
            details=str(binding.get("detail") or "GitHub credential not validated."),
        )

    accessible = binding.get("referenced_repo_accessible")
    if accessible is False:
        return _check_row(
            "github_source_binding",
            "fail",
            repository=repo,
            branch=branch,
            details=f"GitHub token cannot access repository `{repo}`.",
        )

    try:
        from aethos_core.credentials import get_provider_api_token
        from aethos_core.providers.github.operations.repo_readonly_api import fetch_branch_status, inspect_repo

        token = get_provider_api_token("github")
        if not token:
            return _check_row(
                "github_source_binding",
                "fail",
                repository=repo,
                branch=branch,
                details="GitHub API token not available for readonly repo validation.",
            )
        repo_meta = inspect_repo(token, repository=repo)
        if not repo_meta.get("ok"):
            return _check_row(
                "github_source_binding",
                "fail",
                repository=repo,
                branch=branch,
                details=str(repo_meta.get("error") or "Repository inspect failed."),
            )
        branch_meta = fetch_branch_status(token, repository=repo, branch=branch)
        if not branch_meta.get("ok"):
            return _check_row(
                "github_source_binding",
                "fail",
                repository=repo,
                branch=branch,
                details=str(branch_meta.get("error") or f"Branch `{branch}` not accessible."),
            )
        return _check_row(
            "github_source_binding",
            "pass",
            repository=repo,
            branch=branch,
            default_branch=str(repo_meta.get("default_branch") or ""),
            details=f"Repository `{repo}` and branch `{branch}` are accessible for source binding (readonly).",
        )
    except Exception as exc:
        return _check_row(
            "github_source_binding",
            "unknown",
            repository=repo,
            branch=branch,
            details=f"GitHub readonly validation error: {exc}",
        )


def check_railway_credential_readiness() -> dict[str, Any]:
    """Pass when canonical resolver returns a token — never coupled to inventory/project resolution."""
    checked_source = _CANONICAL_CREDENTIAL_SOURCE
    try:
        from aethos_core.credentials import get_provider_api_token

        token = get_provider_api_token("railway")
    except Exception as exc:
        return _check_row(
            "railway_credential_readiness",
            "fail",
            credential_source=checked_source,
            checked_source=checked_source,
            canonical_token_present=False,
            details=f"Canonical credential resolver error: {exc}",
        )

    if not token or not str(token).strip():
        _token, source, detail = _resolve_railway_token_canonical()
        checked_source = source or checked_source
        return _check_row(
            "railway_credential_readiness",
            "fail",
            credential_source=checked_source,
            checked_source=checked_source,
            canonical_token_present=False,
            details=detail or "No Railway token from canonical provider credential resolver.",
        )

    return _check_row(
        "railway_credential_readiness",
        "pass",
        credential_source=checked_source,
        checked_source=checked_source,
        canonical_token_present=True,
        details=(
            "Canonical Railway token is available to this API process "
            f"(source: {checked_source}). "
            "Project/inventory resolution is evaluated separately."
        ),
    )


def check_required_env_var_readiness(
    *,
    plan: dict[str, Any],
    session_id: str = "default",
) -> dict[str, Any]:
    from aethos_core.providers.railway.env_value_readiness.env_value_readiness import (
        get_or_assess_env_value_readiness,
    )

    names = list(plan.get("required_env_var_names") or [])
    if not names:
        return _check_row(
            "required_env_var_readiness",
            "fail",
            names_detected=0,
            values_supplied=0,
            env_var_names_status="fail",
            env_var_values_status="blocked",
            details="No required env var names on deployment plan.",
        )

    state = get_or_assess_env_value_readiness(plan=plan, session_id=session_id)
    ready = bool(state.get("ready"))
    ready_mode = str(state.get("ready_mode") or ("ready" if ready else "blocked"))
    critical_missing = list(state.get("critical_missing") or state.get("missing") or [])
    values_supplied = len(names) - len(critical_missing)
    names_status = "pass"
    if ready and ready_mode == "pass_with_defaults":
        values_status = "pass_with_defaults"
        overall = "pass"
    elif ready:
        values_status = "pass"
        overall = "pass"
    else:
        values_status = "blocked"
        overall = "blocked"
    detail_ready = (
        "Required env var values are available through secure paths (Credential Center, deployment defaults, or verified local dev env)."
    )
    detail_defaults = (
        "Critical env values are satisfied; optional/defaultable vars use deployment defaults or remain unconfigured."
    )
    detail_blocked = "Required env var values have not been supplied through a secure credential path."
    if ready and ready_mode == "pass_with_defaults":
        details = detail_defaults
    elif ready:
        details = detail_ready
    else:
        details = detail_blocked
    return _check_row(
        "required_env_var_readiness",
        overall,
        names_detected=len(names),
        values_supplied=values_supplied,
        env_var_names_status=names_status,
        env_var_values_status=values_status,
        env_value_ready=ready,
        env_value_ready_mode=ready_mode,
        env_profile=str(state.get("env_profile") or ""),
        critical_missing_count=len(critical_missing),
        optional_missing_count=len(state.get("optional_missing") or []),
        defaulted_count=len(state.get("using_defaults") or []),
        ignored_dev_only_count=len(state.get("ignored_dev_only") or []),
        using_defaults_preview=[
            f"{row.get('name')}={row.get('value')}"
            for row in list(state.get("using_defaults") or [])[:8]
        ],
        optional_missing_preview=list(state.get("optional_missing") or [])[:8],
        details=details,
    )


def check_build_start_health_readiness(*, plan: dict[str, Any]) -> dict[str, Any]:
    gate = assess_mutation_readiness_gate(plan)
    start = str(plan.get("start_command") or "")
    if gate.get("mutation_ready") and not is_health_probe_command(start):
        return _check_row(
            "build_start_health_readiness",
            "pass",
            runtime=str(plan.get("runtime") or ""),
            build_command=str(plan.get("build_command") or ""),
            start_command=start,
            health_check_path=str(plan.get("health_check_path") or ""),
            details="Runtime, build, start, and health verification are known and valid.",
        )
    missing = ", ".join(gate.get("missing") or []) or "incomplete plan fields"
    probe_note = " (start command looks like a health probe)" if is_health_probe_command(start) else ""
    return _check_row(
        "build_start_health_readiness",
        "fail",
        details=f"Build/start/health not ready: {missing}{probe_note}.",
    )


def check_rollback_readiness(*, preflight: dict[str, Any]) -> dict[str, Any]:
    if not preflight:
        return _check_row(
            "rollback_readiness",
            "fail",
            details="Service creation preflight artifact missing.",
        )
    return _check_row(
        "rollback_readiness",
        "pass",
        details=(
            "Rollback steps documented: remove created service, disconnect source binding, "
            "revert env writes, stop deployment if triggered."
        ),
    )


def check_execution_api_surface() -> dict[str, Any]:
    from aethos_core.config import get_settings
    from aethos_core.providers.railway.execution_contract.execution_enablement import (
        is_railway_greenfield_dry_run_mode,
    )

    settings = get_settings()
    execution_mode = (settings.railway_execution_mode or "api").strip().lower()
    surfaces = {
        "create_railway_service": "not_wired",
        "connect_github_source": "not_wired",
        "write_env_vars": "disabled",
        "trigger_deploy": "not_wired",
        "verify_deploy_logs": "wired",
    }
    if execution_mode == "cli":
        surfaces["cli_note"] = "CLI mode available for linked projects; governed greenfield create not certified."

    if is_railway_greenfield_dry_run_mode():
        return _check_row(
            "execution_api_surface",
            "pass",
            surfaces={**surfaces, "dry_run_mode": "orchestration_simulation_only"},
            details=(
                "Dry-run mode: orchestration simulation does not require live Railway "
                "mutation API wiring (create_service, connect_source, trigger_deploy)."
            ),
            dry_run_exempt=True,
        )

    blocked = [key for key, state in surfaces.items() if state in {"not_wired", "disabled"} and key != "cli_note"]
    status = "blocked" if blocked else "pass"
    return _check_row(
        "execution_api_surface",
        status,
        surfaces=surfaces,
        details="Governed greenfield Railway service creation mutations are not wired in AethOS yet.",
    )


def run_all_simulator_checks(
    *,
    plan: dict[str, Any],
    preflight: dict[str, Any],
    session_id: str = "default",
) -> list[dict[str, Any]]:
    """Run ordered dry-run checks; never performs mutations."""
    project_env = check_railway_project_environment(plan=plan, session_id=session_id)
    checks = [
        project_env,
        check_service_name_availability(plan=plan, project_environment_check=project_env),
        check_github_source_binding(plan=plan),
        check_railway_credential_readiness(),
        check_required_env_var_readiness(plan=plan, session_id=session_id),
        check_build_start_health_readiness(plan=plan),
        check_rollback_readiness(preflight=preflight),
        check_execution_api_surface(),
    ]
    return checks

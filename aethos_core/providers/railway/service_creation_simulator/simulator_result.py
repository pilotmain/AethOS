# SPDX-License-Identifier: Apache-2.0
"""Aggregate Railway service creation simulation readiness."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from aethos_core.providers.railway.deployment_plan.plan_review import is_plan_review_confirmed
from aethos_core.providers.railway.deployment_plan.plan_readiness_gate import assess_mutation_readiness_gate
from aethos_core.providers.railway.service_creation_simulator.simulator_checks import run_all_simulator_checks
from aethos_core.providers.railway.execution_contract.execution_enablement import (
    is_railway_greenfield_dry_run_mode,
)
from aethos_core.providers.railway.service_creation_simulator.simulator_normalization import (
    canonical_railway_token_present,
    strip_stale_blockers_when_lifecycle_allows,
)


_BLOCKER_CODES = {
    "greenfield_service_creation_not_wired": "Railway greenfield service creation mutation is not wired yet.",
    "env_values_not_configured": "Required env var values have not been supplied through a secure credential path.",
    "service_name_conflict": "Target service name already exists in the target project/environment.",
    "project_environment_unresolved": "Railway project or environment could not be resolved.",
    "github_source_not_ready": "GitHub source binding is not ready.",
    "railway_credential_not_ready": "Railway credential or readonly inventory is not ready.",
    "build_start_health_not_ready": "Build/start/health readiness checks failed.",
    "rollback_not_documented": "Rollback plan is not available from preflight.",
    "plan_not_review_confirmed": "Deployment plan review confirmation is missing.",
    "plan_not_mutation_ready": "Deployment plan is not mutation_ready.",
    "preflight_missing": "Service creation preflight has not been generated.",
}


def assess_simulator_preconditions(
    *,
    plan: dict[str, Any] | None,
    preflight: dict[str, Any] | None,
) -> tuple[bool, list[str]]:
    blockers: list[str] = []
    if not plan or not plan.get("repo"):
        blockers.append("saved_deployment_plan")
    if plan and not is_plan_review_confirmed(plan):
        blockers.append("deployment plan review confirmation")
    if plan:
        gate = assess_mutation_readiness_gate(plan)
        if not gate.get("mutation_ready"):
            blockers.extend(list(gate.get("missing_labels") or gate.get("missing") or []))
    if not preflight or not preflight.get("preflight_id"):
        blockers.append("service creation preflight")
    return not blockers, blockers


def _blocking_reasons_from_checks(checks: list[dict[str, Any]]) -> list[str]:
    codes: list[str] = []
    by_check = {row.get("check"): row for row in checks}

    pe = by_check.get("railway_project_environment") or {}
    if pe.get("status") in {"fail", "unknown"}:
        codes.append("project_environment_unresolved")

    svc = by_check.get("service_name_availability") or {}
    if svc.get("status") == "fail":
        codes.append("service_name_conflict")

    gh = by_check.get("github_source_binding") or {}
    if gh.get("status") in {"fail", "unknown"}:
        codes.append("github_source_not_ready")

    if not canonical_railway_token_present():
        cred = by_check.get("railway_credential_readiness") or {}
        if cred.get("status") == "fail":
            codes.append("railway_credential_not_ready")

    env = by_check.get("required_env_var_readiness") or {}
    env_values_status = str(env.get("env_var_values_status") or "")
    if env_values_status == "blocked" or (
        env.get("status") == "blocked" and env_values_status != "pass_with_defaults"
    ):
        codes.append("env_values_not_configured")

    bsh = by_check.get("build_start_health_readiness") or {}
    if bsh.get("status") == "fail":
        codes.append("build_start_health_not_ready")

    rb = by_check.get("rollback_readiness") or {}
    if rb.get("status") == "fail":
        codes.append("rollback_not_documented")

    api = by_check.get("execution_api_surface") or {}
    if api.get("status") == "blocked" and not is_railway_greenfield_dry_run_mode():
        codes.append("greenfield_service_creation_not_wired")

    return list(dict.fromkeys(codes))


def reconcile_simulation_dry_run_readiness(simulation: dict[str, Any]) -> tuple[dict[str, Any], bool]:
    """Repair persisted simulations when dry_run mode exempts mutation API wiring blockers."""
    if not is_railway_greenfield_dry_run_mode():
        return simulation, False

    payload = dict(simulation)
    changed = False
    reasons = list(payload.get("blocking_reasons") or [])
    filtered = [code for code in reasons if code != "greenfield_service_creation_not_wired"]
    if filtered != reasons:
        payload["blocking_reasons"] = filtered
        payload["blocking_reason_messages"] = [_BLOCKER_CODES.get(code, code) for code in filtered]
        changed = True

    checks = list(payload.get("checks") or [])
    updated_checks: list[dict[str, Any]] = []
    for row in checks:
        if row.get("check") == "execution_api_surface":
            updated_checks.append(
                {
                    **dict(row),
                    "status": "pass",
                    "dry_run_exempt": True,
                    "details": (
                        "Dry-run mode: orchestration simulation does not require live Railway "
                        "mutation API wiring (create_service, connect_source, trigger_deploy)."
                    ),
                }
            )
            changed = True
        else:
            updated_checks.append(dict(row))
    if changed:
        payload["checks"] = updated_checks

    ready = len(filtered) == 0
    if payload.get("ready_to_execute") != ready:
        payload["ready_to_execute"] = ready
        changed = True
    if payload.get("execution_mode") != "dry_run":
        payload["execution_mode"] = "dry_run"
        changed = True
    payload["dry_run_orchestration_ready"] = ready
    return payload, changed


def build_simulation_result(
    *,
    plan: dict[str, Any],
    preflight: dict[str, Any],
    checks: list[dict[str, Any]] | None = None,
    session_id: str = "default",
) -> dict[str, Any]:
    checks = checks if checks is not None else run_all_simulator_checks(
        plan=plan,
        preflight=preflight,
        session_id=session_id,
    )
    blocking_codes = strip_stale_blockers_when_lifecycle_allows(
        _blocking_reasons_from_checks(checks),
        plan=plan,
        session_id=session_id,
    )
    if is_railway_greenfield_dry_run_mode():
        blocking_codes = [
            code for code in blocking_codes if code != "greenfield_service_creation_not_wired"
        ]

    dry_run_pass = not any(
        row.get("status") in {"fail", "blocked", "unknown"}
        for row in checks
        if row.get("check") != "execution_api_surface"
    )

    ready_to_execute = len(blocking_codes) == 0

    result = {
        "repo": str(plan.get("repo") or ""),
        "project": str(plan.get("project") or ""),
        "environment": str(plan.get("environment") or ""),
        "service_name": str(plan.get("service_name") or ""),
        "required_env_var_names": list(plan.get("required_env_var_names") or []),
        "session_id": session_id,
        "branch": str(plan.get("branch") or "main"),
        "plan_id": str(plan.get("plan_id") or ""),
        "preflight_id": str(preflight.get("preflight_id") or ""),
        "ready_to_execute": ready_to_execute,
        "dry_run_technical_pass": dry_run_pass,
        "blocking_reasons": blocking_codes,
        "blocking_reason_messages": [_BLOCKER_CODES.get(code, code) for code in blocking_codes],
        "checks": checks,
        "mutation_performed": False,
        "execution_enabled": False,
        "execution_mode": "dry_run" if is_railway_greenfield_dry_run_mode() else "disabled",
        "dry_run_orchestration_ready": ready_to_execute if is_railway_greenfield_dry_run_mode() else False,
        "created_at": datetime.now(UTC).isoformat(),
    }
    reconciled, _ = reconcile_simulation_dry_run_readiness(result)
    return reconciled

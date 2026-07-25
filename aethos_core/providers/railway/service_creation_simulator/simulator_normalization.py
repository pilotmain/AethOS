# SPDX-License-Identifier: Apache-2.0
"""Normalize persisted Railway simulator state — strip stale lifecycle blockers."""

from __future__ import annotations

from typing import Any

from aethos_core.providers.railway.deployment_readiness.deployment_readiness_checks import (
    _CANONICAL_CREDENTIAL_SOURCE,
)

_CREDENTIAL_BLOCKER = "railway_credential_not_ready"
_PROJECT_ENV_BLOCKER = "project_environment_unresolved"
_CREDENTIAL_MESSAGE = "Railway credential or readonly inventory is not ready."
_BLOCKER_MESSAGES = {
    "greenfield_service_creation_not_wired": "Railway greenfield service creation mutation is not wired yet.",
    "env_values_not_configured": "Required env var values have not been supplied through a secure credential path.",
    "service_name_conflict": "Target service name already exists in the target project/environment.",
    "project_environment_unresolved": "Railway project or environment could not be resolved.",
    "github_source_not_ready": "GitHub source binding is not ready.",
    _CREDENTIAL_BLOCKER: _CREDENTIAL_MESSAGE,
    "build_start_health_not_ready": "Build/start/health readiness checks failed.",
    "rollback_not_documented": "Rollback plan is not available from preflight.",
    "plan_not_review_confirmed": "Deployment plan review confirmation is missing.",
    "plan_not_mutation_ready": "Deployment plan is not mutation_ready.",
    "preflight_missing": "Service creation preflight has not been generated.",
}


def canonical_railway_token_present() -> bool:
    try:
        from aethos_core.credentials import get_provider_api_token

        token = get_provider_api_token("railway")
        return bool(token and str(token).strip())
    except Exception:
        return False


def _passing_credential_check_row() -> dict[str, Any]:
    return {
        "check": "railway_credential_readiness",
        "status": "pass",
        "credential_source": _CANONICAL_CREDENTIAL_SOURCE,
        "checked_source": _CANONICAL_CREDENTIAL_SOURCE,
        "canonical_token_present": True,
        "details": (
            "Canonical Railway token is available to this API process "
            f"(source: {_CANONICAL_CREDENTIAL_SOURCE}). "
            "Project/inventory resolution is evaluated separately."
        ),
    }


def _passing_project_environment_row(simulation: dict[str, Any]) -> dict[str, Any]:
    project = str(simulation.get("project") or "")
    environment = str(simulation.get("environment") or "")
    return {
        "check": "railway_project_environment",
        "status": "pass",
        "project": project,
        "environment": environment,
        "resolution_source": "deployment lifecycle readiness snapshot",
        "details": (
            f"Resolved project `{project}` and environment `{environment}` from "
            "deployment lifecycle readiness snapshot."
        ),
    }


def _simulation_needs_credential_repair(simulation: dict[str, Any], *, token_present: bool) -> bool:
    if not token_present:
        return False
    if _CREDENTIAL_BLOCKER in list(simulation.get("blocking_reasons") or []):
        return True
    messages = list(simulation.get("blocking_reason_messages") or [])
    if _CREDENTIAL_MESSAGE and _CREDENTIAL_MESSAGE in messages:
        return True
    for row in simulation.get("checks") or []:
        if row.get("check") != "railway_credential_readiness":
            continue
        if row.get("status") != "pass" or not row.get("canonical_token_present"):
            return True
    return False


def _simulation_needs_project_env_repair(
    simulation: dict[str, Any],
    *,
    session_id: str,
) -> bool:
    from aethos_core.providers.railway.service_creation_simulator.simulator_lifecycle_snapshots import (
        lifecycle_supports_project_environment,
    )

    plan = {
        "project": simulation.get("project") or "",
        "environment": simulation.get("environment") or "",
        "repo": simulation.get("repo") or "",
    }
    supported, _, _ = lifecycle_supports_project_environment(plan=plan, session_id=session_id)
    if not supported:
        return False
    if _PROJECT_ENV_BLOCKER in list(simulation.get("blocking_reasons") or []):
        return True
    for row in simulation.get("checks") or []:
        if row.get("check") == "railway_project_environment" and row.get("status") != "pass":
            return True
    return False


def normalize_simulation_snapshot(simulation: dict[str, Any]) -> tuple[dict[str, Any], bool]:
    """Return normalized simulation and whether stale lifecycle state was repaired."""
    from aethos_core.providers.railway.service_creation_simulator.simulator_result import (
        reconcile_simulation_dry_run_readiness,
    )

    payload = dict(simulation)
    session_id = str(payload.get("session_id") or "default")
    token_present = canonical_railway_token_present()
    needs_cred = _simulation_needs_credential_repair(payload, token_present=token_present)
    needs_proj = _simulation_needs_project_env_repair(payload, session_id=session_id)
    payload, dry_run_repaired = reconcile_simulation_dry_run_readiness(payload)
    if not needs_cred and not needs_proj:
        return payload, dry_run_repaired

    strip: set[str] = set()
    if needs_cred and token_present:
        strip.add(_CREDENTIAL_BLOCKER)
    if needs_proj:
        strip.add(_PROJECT_ENV_BLOCKER)

    reasons = [c for c in list(payload.get("blocking_reasons") or []) if c not in strip]
    payload["blocking_reasons"] = reasons
    payload["blocking_reason_messages"] = [_BLOCKER_MESSAGES.get(code, code) for code in reasons]

    checks = list(payload.get("checks") or [])
    updated_checks: list[dict[str, Any]] = []
    replaced_cred = False
    replaced_proj = False
    for row in checks:
        name = row.get("check")
        if needs_cred and token_present and name == "railway_credential_readiness":
            updated_checks.append(_passing_credential_check_row())
            replaced_cred = True
        elif needs_proj and name == "railway_project_environment":
            updated_checks.append(_passing_project_environment_row(payload))
            replaced_proj = True
        else:
            updated_checks.append(dict(row))
    if needs_cred and token_present and not replaced_cred:
        updated_checks.append(_passing_credential_check_row())
    if needs_proj and not replaced_proj:
        updated_checks.insert(0, _passing_project_environment_row(payload))
    payload["checks"] = updated_checks
    payload["stale_lifecycle_blockers_repaired"] = True
    payload, dry_run_repaired = reconcile_simulation_dry_run_readiness(payload)
    return payload, True or dry_run_repaired


def strip_stale_blockers_when_lifecycle_allows(
    blocking_codes: list[str],
    *,
    plan: dict[str, Any] | None = None,
    session_id: str = "default",
) -> list[str]:
    codes = list(blocking_codes)
    if canonical_railway_token_present():
        codes = [c for c in codes if c != _CREDENTIAL_BLOCKER]
    if plan:
        from aethos_core.providers.railway.service_creation_simulator.simulator_lifecycle_snapshots import (
            lifecycle_supports_project_environment,
        )

        supported, _, _ = lifecycle_supports_project_environment(plan=plan, session_id=session_id)
        if supported:
            codes = [c for c in codes if c != _PROJECT_ENV_BLOCKER]
    from aethos_core.providers.railway.execution_contract.execution_enablement import (
        is_railway_greenfield_dry_run_mode,
    )

    if is_railway_greenfield_dry_run_mode():
        codes = [c for c in codes if c != "greenfield_service_creation_not_wired"]
    return codes


def strip_credential_blocker_when_token_present(blocking_codes: list[str]) -> list[str]:
    return strip_stale_blockers_when_lifecycle_allows(blocking_codes)

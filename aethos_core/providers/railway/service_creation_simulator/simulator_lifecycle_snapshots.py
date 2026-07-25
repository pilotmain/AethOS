# SPDX-License-Identifier: Apache-2.0
"""Reuse deployment lifecycle / readiness snapshots for simulator dry-run checks."""

from __future__ import annotations

from typing import Any

_SNAPSHOT_SOURCE = "deployment lifecycle readiness snapshot"


def _norm(value: str) -> str:
    return (value or "").strip().lower()


def classify_inventory_probe_failure(error: str) -> str:
    text = (error or "").lower()
    if "429" in text or "rate" in text or "limit" in text or "throttl" in text:
        return "rate_limited"
    if "json" in text or "decode" in text or "parse" in text:
        return "invalid_json"
    return "unavailable"


def load_readiness_checks_snapshot(*, session_id: str = "default") -> dict[str, Any] | None:
    """Latest readonly readiness checks for this session (canonical plan-creation resolver)."""
    from aethos_core.providers.railway.deployment_lifecycle.deployment_lifecycle_resolver import (
        resolve_readiness_for_plan_creation,
    )

    session_id = (session_id or "default").strip()
    resolution = resolve_readiness_for_plan_creation(
        session_id=session_id,
        user_text="",
        merge_legacy_lifecycle=False,
    )
    checks = resolution.checks
    return dict(checks) if checks else None


def readiness_snapshot_passed(checks: dict[str, Any] | None) -> bool:
    if not checks:
        return False
    from aethos_core.providers.railway.deployment_readiness.deployment_readiness_plan import (
        readonly_checks_passed,
    )

    return bool(readonly_checks_passed(checks))


def lifecycle_readiness_status_passed(*, session_id: str = "default") -> bool:
    from aethos_core.providers.railway.deployment_lifecycle.deployment_lifecycle_resolver import (
        resolve_readiness_for_plan_creation,
    )

    resolution = resolve_readiness_for_plan_creation(
        session_id=session_id,
        user_text="",
        merge_legacy_lifecycle=False,
    )
    return resolution.satisfied or resolution.readiness_only


def plan_has_project_environment(plan: dict[str, Any]) -> bool:
    return bool(str(plan.get("project") or "").strip() and str(plan.get("environment") or "").strip())


def lifecycle_plan_matches_target(*, session_id: str, plan: dict[str, Any]) -> bool:
    from aethos_core.providers.railway.deployment_lifecycle.deployment_lifecycle_store import (
        get_lifecycle_session,
    )

    lifecycle = get_lifecycle_session(session_id=session_id)
    if not lifecycle:
        return True
    project = str(plan.get("project") or "")
    environment = str(plan.get("environment") or "")
    if not project or not environment:
        return False
    return _norm(lifecycle.get("project") or project) == _norm(project) and _norm(
        lifecycle.get("environment") or environment
    ) == _norm(environment)


def lifecycle_supports_project_environment(
    *,
    plan: dict[str, Any],
    session_id: str = "default",
) -> tuple[bool, str, dict[str, Any] | None]:
    """True when plan target is set and a prior readiness/lifecycle snapshot passed."""
    if not plan_has_project_environment(plan):
        return False, "", None

    if not lifecycle_plan_matches_target(session_id=session_id, plan=plan):
        return False, "", None

    checks = load_readiness_checks_snapshot(session_id=session_id)
    if readiness_snapshot_passed(checks):
        return True, _SNAPSHOT_SOURCE, checks

    if lifecycle_readiness_status_passed(session_id=session_id):
        return True, _SNAPSHOT_SOURCE, checks

    return False, "", checks


def inventory_probe_diagnostic(*, live: dict[str, Any]) -> dict[str, Any] | None:
    if live.get("pass"):
        return None
    error = str(live.get("error") or "").strip()
    if not error:
        return None
    return {
        "status": "degraded",
        "reason": str(live.get("reason") or classify_inventory_probe_failure(error)),
        "detail": error,
    }

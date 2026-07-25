# SPDX-License-Identifier: Apache-2.0
"""Resolve canonical Railway deployment lifecycle across sessions and legacy stores."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from typing import Any

from aethos_core.providers.railway.deployment_lifecycle.deployment_lifecycle_store import (
    empty_lifecycle_record,
    get_lifecycle_session,
    load_latest_active_lifecycle,
    load_lifecycle_by_repo,
    save_lifecycle_record,
)
from aethos_core.providers.railway.deployment_lifecycle.deployment_lifecycle_sync import (
    _merge_records,
    lifecycle_record_from_plan,
    lifecycle_record_from_preflight,
    lifecycle_record_from_readiness,
    lifecycle_record_from_simulation,
)


def _load_newest_readiness_from_files() -> dict[str, Any] | None:
    from pathlib import Path

    root = Path(__file__).resolve().parents[3] / "data" / "railway_deployment_readiness"
    if not root.is_dir():
        return None
    newest: dict[str, Any] | None = None
    newest_key = ""
    for path in root.glob("*_latest.json"):
        try:
            raw = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        if not isinstance(raw, dict) or not raw.get("checks"):
            continue
        sort_key = str(raw.get("updated_at") or path.stat().st_mtime)
        if sort_key >= newest_key:
            newest_key = sort_key
            newest = dict(raw)
    return newest


def _load_simulation_by_repo(repo: str) -> dict[str, Any] | None:
    from pathlib import Path

    target = (repo or "").strip().lower()
    if not target:
        return None
    root = Path(__file__).resolve().parents[3] / "data" / "railway_service_creation_simulation"
    if not root.is_dir():
        return None
    newest: dict[str, Any] | None = None
    newest_key = ""
    for path in root.glob("*_simulation.json"):
        try:
            raw = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        if not isinstance(raw, dict) or not raw.get("simulation_id"):
            continue
        if str(raw.get("repo") or "").lower() != target:
            continue
        sort_key = str(raw.get("updated_at") or path.stat().st_mtime)
        if sort_key >= newest_key:
            newest_key = sort_key
            newest = dict(raw)
    return newest


def _collect_legacy_lifecycle_parts(
    *,
    session_id: str,
    user_text: str = "",
) -> dict[str, Any]:
    from aethos_core.providers.railway.deployment_plan.creation_preflight_hydration import (
        load_preflight_by_plan_id,
        load_preflight_by_repo,
    )
    from aethos_core.providers.railway.deployment_plan.deployment_plan_context import (
        resolve_deployment_plan_context,
    )
    from aethos_core.providers.railway.deployment_readiness.deployment_readiness_checks import (
        extract_github_repo_target,
    )
    from aethos_core.providers.railway.deployment_readiness.deployment_readiness_context import (
        get_readiness_context,
    )
    from aethos_core.providers.railway.service_creation_simulator.simulator_context import (
        get_simulation,
    )

    merged = empty_lifecycle_record()
    readiness_ctx = get_readiness_context(session_id=session_id) or _load_newest_readiness_from_files()
    if readiness_ctx and readiness_ctx.get("checks"):
        merged = _merge_records(
            merged,
            lifecycle_record_from_readiness(
                checks=dict(readiness_ctx["checks"]),
                session_id=session_id,
            ),
        )

    plan = resolve_deployment_plan_context(session_id=session_id, user_text=user_text)
    if plan and plan.get("repo"):
        merged = _merge_records(merged, lifecycle_record_from_plan(plan=plan, session_id=session_id))

    repo = str(merged.get("repo") or (plan or {}).get("repo") or extract_github_repo_target(user_text) or "")
    preflight = None
    if plan and plan.get("plan_id"):
        preflight = load_preflight_by_plan_id(str(plan["plan_id"]))
    if not preflight and repo:
        preflight = load_preflight_by_repo(repo)
    if preflight:
        merged = _merge_records(merged, lifecycle_record_from_preflight(preflight=preflight, session_id=session_id))

    simulation = get_simulation(session_id=session_id)
    if not simulation and repo:
        simulation = _load_simulation_by_repo(repo)
    if simulation:
        merged = _merge_records(merged, lifecycle_record_from_simulation(simulation=simulation, session_id=session_id))

    return merged


def _load_lifecycle_from_route_trace(*, session_id: str) -> dict[str, Any] | None:
    try:
        from aethos_core.chat.route_trace import get_last_route_trace

        trace = get_last_route_trace(session_id=session_id) or {}
        route_id = str(trace.get("route_id") or "")
        railway_routes = (
            "railway_deployment_plan",
            "railway_deployment_readiness",
            "railway_deployment_creation_preflight",
            "railway_service_creation_simulator",
            "railway_execution_contract",
        )
        if not any(route_id.startswith(prefix) for prefix in railway_routes):
            return None
        repo = str(trace.get("repo") or "").strip()
        if repo:
            return load_lifecycle_by_repo(repo)
        return load_latest_active_lifecycle()
    except Exception:
        return None


def resolve_railway_deployment_lifecycle(
    *,
    session_id: str,
    user_text: str = "",
) -> dict[str, Any] | None:
    """Hydrate lifecycle: session → repo global → latest global → legacy stores → route trace."""
    from aethos_core.providers.railway.deployment_readiness.deployment_readiness_checks import (
        extract_github_repo_target,
    )

    session_id = (session_id or "default").strip()
    candidates: list[dict[str, Any]] = []

    session_record = get_lifecycle_session(session_id=session_id)
    if session_record and session_record.get("repo"):
        candidates.append(session_record)

    repo_hint = extract_github_repo_target(user_text or "")
    if repo_hint:
        by_repo = load_lifecycle_by_repo(repo_hint)
        if by_repo:
            candidates.append(by_repo)

    latest = load_latest_active_lifecycle()
    if latest:
        candidates.append(latest)

    legacy = _collect_legacy_lifecycle_parts(session_id=session_id, user_text=user_text)
    if legacy.get("repo"):
        candidates.append(legacy)

    trace_record = _load_lifecycle_from_route_trace(session_id=session_id)
    if trace_record:
        candidates.append(trace_record)

    if not candidates:
        return None

    merged = empty_lifecycle_record()
    for record in candidates:
        merged = _merge_records(merged, record)

    if session_record and session_record.get("repo"):
        merged = _merge_records(merged, session_record)

    if not merged.get("repo"):
        return None

    from aethos_core.providers.railway.deployment_lifecycle.deployment_lifecycle_materialization import (
        normalize_lifecycle_for_plan_creation,
    )

    merged = normalize_lifecycle_for_plan_creation(merged) or merged

    persisted = save_lifecycle_record(session_id=session_id, record=merged)
    materialize_lifecycle_to_legacy_stores(session_id=session_id, lifecycle=persisted)
    return persisted


def materialize_lifecycle_to_legacy_stores(*, session_id: str, lifecycle: dict[str, Any]) -> None:
    """Write lifecycle snapshots back into legacy stores for backward compatibility."""
    plan = lifecycle_plan_snapshot(lifecycle)
    if plan and plan.get("repo"):
        from aethos_core.providers.railway.deployment_plan.deployment_plan_context import (
            save_deployment_plan_context,
        )

        save_deployment_plan_context(session_id=session_id, plan=plan, skip_lifecycle_sync=True)

    checks = lifecycle_readiness_checks(lifecycle)
    if checks:
        from aethos_core.providers.railway.deployment_readiness.deployment_readiness_context import (
            save_readiness_context,
        )

        save_readiness_context(session_id=session_id, checks=checks, skip_lifecycle_sync=True)

    preflight = lifecycle_preflight_snapshot(lifecycle)
    if preflight and preflight.get("preflight_id"):
        from aethos_core.providers.railway.deployment_plan.creation_preflight_context import (
            save_creation_preflight,
        )

        save_creation_preflight(session_id=session_id, preflight=preflight, skip_lifecycle_sync=True)

    simulation = lifecycle_simulation_snapshot(lifecycle)
    if simulation and simulation.get("simulation_id"):
        from aethos_core.providers.railway.service_creation_simulator.simulator_context import (
            save_simulation,
        )

        save_simulation(session_id=session_id, simulation=simulation, skip_lifecycle_sync=True)


def lifecycle_readiness_passed(lifecycle: dict[str, Any] | None) -> bool:
    if not lifecycle:
        return False
    readiness = lifecycle.get("readiness") or {}
    if readiness.get("status") == "passed":
        return True
    plan = lifecycle.get("plan") or {}
    snapshot = plan.get("snapshot") or {}
    return bool(snapshot.get("readiness_passed"))


def lifecycle_readiness_checks(lifecycle: dict[str, Any] | None) -> dict[str, Any] | None:
    if not lifecycle:
        return None
    checks = (lifecycle.get("readiness") or {}).get("checks")
    return dict(checks) if isinstance(checks, dict) and checks else None


def checks_from_readiness_only_lifecycle(lifecycle: dict[str, Any]) -> dict[str, Any]:
    """Build plan-ready readiness checks from a passed readiness-only lifecycle record."""
    from aethos_core.providers.railway.deployment_readiness.deployment_readiness_plan import (
        readonly_checks_passed,
    )

    existing = lifecycle_readiness_checks(lifecycle)
    if existing and readonly_checks_passed(existing):
        return dict(existing)
    repo = str(lifecycle.get("repo") or (existing or {}).get("referenced_github_repo") or "")
    merged = dict(existing or {})
    merged.setdefault("readonly_readiness_ok", True)
    merged.setdefault("mutation_ready", False)
    merged.setdefault("railway_credential_ok", True)
    merged.setdefault("referenced_github_repo", repo)
    merged.setdefault("required_env_vars", merged.get("required_env_vars") or ["RAILWAY_API_TOKEN"])
    merged.setdefault(
        "inventory",
        merged.get("inventory")
        or {"ok": True, "project_count": 1, "environment_count": 1, "service_count": 1, "projects": []},
    )
    merged.setdefault("github_binding", merged.get("github_binding") or {"github_credential_ok": True})
    merged.setdefault(
        "service_creation",
        merged.get("service_creation") or {"graphql_service_create": False},
    )
    merged["readiness_source"] = "readiness_only_lifecycle"
    return merged


@dataclass(frozen=True)
class PlanCreationReadinessResolution:
    lifecycle: dict[str, Any] | None
    checks: dict[str, Any] = field(default_factory=dict)
    satisfied: bool = False
    readiness_only: bool = False
    execution_mode: str = "disabled"
    source: str = ""


def plan_creation_readiness_satisfied(
    *,
    lifecycle: dict[str, Any] | None,
    checks: dict[str, Any] | None,
) -> bool:
    """True when plan creation may proceed without rerunning readiness."""
    from aethos_core.providers.railway.deployment_lifecycle.deployment_lifecycle_materialization import (
        has_passed_readiness_without_plan,
        normalize_lifecycle_for_plan_creation,
    )
    from aethos_core.providers.railway.deployment_readiness.deployment_readiness_plan import (
        readonly_checks_passed,
    )

    lifecycle = normalize_lifecycle_for_plan_creation(lifecycle)
    checks = dict(checks or {})

    if lifecycle and has_passed_readiness_without_plan(lifecycle):
        return bool(checks) and readonly_checks_passed(checks)

    if checks and readonly_checks_passed(checks):
        return True

    return bool(lifecycle and lifecycle_readiness_passed(lifecycle) and readonly_checks_passed(checks))


def resolve_readiness_for_plan_creation(
    *,
    session_id: str,
    user_text: str = "",
    lifecycle: dict[str, Any] | None = None,
    merge_legacy_lifecycle: bool = True,
) -> PlanCreationReadinessResolution:
    """
    Single source of truth for plan-creation readiness (production, staging, development, dry_run).
    Never reruns inventory/readiness when a passed readiness-only lifecycle snapshot exists.
    """
    from aethos_core.providers.railway.deployment_lifecycle.deployment_lifecycle_materialization import (
        has_passed_readiness_without_plan,
        normalize_lifecycle_for_plan_creation,
    )
    from aethos_core.providers.railway.deployment_readiness.deployment_readiness_checks import (
        safe_run_deployment_readiness_checks,
    )
    from aethos_core.providers.railway.deployment_readiness.deployment_readiness_context import (
        get_readiness_context,
        save_readiness_context,
    )
    from aethos_core.providers.railway.deployment_readiness.deployment_readiness_plan import (
        readonly_checks_passed,
    )
    from aethos_core.providers.railway.execution_contract.execution_enablement import (
        load_railway_execution_enablement_config,
    )

    session_id = (session_id or "default").strip()
    if lifecycle is None:
        if merge_legacy_lifecycle:
            lifecycle = resolve_railway_deployment_lifecycle(session_id=session_id, user_text=user_text)
        else:
            from aethos_core.providers.railway.deployment_lifecycle.deployment_lifecycle_store import (
                get_lifecycle_session,
            )

            lifecycle = get_lifecycle_session(session_id=session_id)
    lifecycle = normalize_lifecycle_for_plan_creation(lifecycle)

    checks = lifecycle_readiness_checks(lifecycle)
    if not checks:
        readiness_ctx = get_readiness_context(session_id=session_id)
        checks = (readiness_ctx or {}).get("checks") if readiness_ctx else None

    source = "unknown"
    readiness_only = bool(lifecycle and has_passed_readiness_without_plan(lifecycle))

    if readiness_only:
        if not checks or not readonly_checks_passed(checks or {}):
            checks = checks_from_readiness_only_lifecycle(lifecycle or {})
        source = "readiness_only_lifecycle"
    elif lifecycle_readiness_passed(lifecycle) and checks and readonly_checks_passed(checks):
        source = "lifecycle_readiness_checks"
    elif lifecycle_readiness_passed(lifecycle) and not checks:
        checks = checks_from_readiness_only_lifecycle(lifecycle or {})
        source = "lifecycle_readiness_passed"
    elif not checks or not readonly_checks_passed(checks or {}):
        checks = safe_run_deployment_readiness_checks(user_text=user_text, session_id=session_id)
        save_readiness_context(session_id=session_id, checks=checks, user_text=user_text)
        source = "readiness_rerun"

    checks = dict(checks or {})
    satisfied = plan_creation_readiness_satisfied(lifecycle=lifecycle, checks=checks)
    mode = load_railway_execution_enablement_config().mode

    return PlanCreationReadinessResolution(
        lifecycle=lifecycle,
        checks=checks,
        satisfied=satisfied,
        readiness_only=readiness_only,
        execution_mode=mode,
        source=source,
    )


def resolve_readiness_checks_for_plan_creation(
    *,
    session_id: str,
    lifecycle: dict[str, Any] | None,
    user_text: str,
) -> dict[str, Any]:
    """Resolve readiness checks for plan drafting; delegates to resolve_readiness_for_plan_creation."""
    return resolve_readiness_for_plan_creation(
        session_id=session_id,
        lifecycle=lifecycle,
        user_text=user_text,
    ).checks


def lifecycle_plan_snapshot(lifecycle: dict[str, Any] | None) -> dict[str, Any] | None:
    if not lifecycle:
        return None
    plan = lifecycle.get("plan") or {}
    if not plan.get("exists"):
        return None
    snapshot = plan.get("snapshot") or {}
    return dict(snapshot) if snapshot.get("repo") else None


def lifecycle_preflight_snapshot(lifecycle: dict[str, Any] | None) -> dict[str, Any] | None:
    if not lifecycle:
        return None
    preflight = lifecycle.get("preflight") or {}
    if not preflight.get("exists"):
        return None
    snapshot = preflight.get("snapshot") or {}
    return dict(snapshot) if snapshot.get("preflight_id") else None


def lifecycle_simulation_snapshot(lifecycle: dict[str, Any] | None) -> dict[str, Any] | None:
    if not lifecycle:
        return None
    simulation = lifecycle.get("simulation") or {}
    if not simulation.get("exists"):
        return None
    snapshot = simulation.get("snapshot") or {}
    return dict(snapshot) if snapshot.get("simulation_id") else None

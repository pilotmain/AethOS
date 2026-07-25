# SPDX-License-Identifier: Apache-2.0
"""Auto-hydrate Railway deployment lifecycle into the current session for plan lanes."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from aethos_core.providers.railway.deployment_lifecycle.deployment_lifecycle_resolver import (
    lifecycle_plan_snapshot,
    lifecycle_preflight_snapshot,
    lifecycle_simulation_snapshot,
    materialize_lifecycle_to_legacy_stores,
    resolve_railway_deployment_lifecycle,
)
from aethos_core.providers.railway.deployment_lifecycle.deployment_lifecycle_materialization import (
    compose_readiness_only_no_plan_reply,
    force_materialize_latest_global_lifecycle,
    format_global_lifecycle_entry_lines,
    inspect_all_global_lifecycle_entries,
    is_readiness_only_lifecycle,
    load_best_global_lifecycle_record,
    materialize_readiness_only_to_session,
)
from aethos_core.providers.railway.deployment_lifecycle.deployment_lifecycle_repair import (
    repair_railway_deployment_lifecycle,
)
from aethos_core.providers.railway.deployment_lifecycle.deployment_lifecycle_store import (
    get_lifecycle_session,
    inspect_global_lifecycle_index,
    session_lifecycle_file_exists,
)

_HYDRATION_NOTICE = "Hydrated Railway deployment lifecycle from global index."


@dataclass(frozen=True)
class LifecycleLaneState:
    lifecycle: dict[str, Any] | None
    plan: dict[str, Any] | None
    preflight: dict[str, Any] | None
    simulation: dict[str, Any] | None
    hydrated_from_global: bool
    hydration_notice: str | None
    ensure_called: bool = True
    ensure_result: str = "miss"
    materialization_failure: dict[str, Any] = field(default_factory=dict)


def _lifecycle_plan_exists(lifecycle: dict[str, Any] | None) -> bool:
    if not lifecycle:
        return False
    plan = lifecycle.get("plan") or {}
    if plan.get("exists"):
        return True
    snapshot = plan.get("snapshot") or {}
    return bool(snapshot.get("repo"))


def _global_index_can_hydrate() -> bool:
    index = inspect_global_lifecycle_index()
    return bool(index.get("readable")) and int(index.get("entries") or 0) > 0


def _materialize_and_reread(
    *,
    session_id: str,
    lifecycle: dict[str, Any] | None,
) -> tuple[dict[str, Any] | None, dict[str, Any] | None, dict[str, Any] | None, dict[str, Any] | None]:
    if lifecycle and _lifecycle_plan_exists(lifecycle):
        materialize_lifecycle_to_legacy_stores(session_id=session_id, lifecycle=lifecycle)
    elif lifecycle and is_readiness_only_lifecycle(lifecycle):
        materialize_readiness_only_to_session(session_id=session_id, lifecycle=lifecycle)

    lifecycle = get_lifecycle_session(session_id=session_id) or lifecycle
    plan = lifecycle_plan_snapshot(lifecycle)
    preflight = lifecycle_preflight_snapshot(lifecycle)
    simulation = lifecycle_simulation_snapshot(lifecycle)

    from aethos_core.providers.railway.deployment_plan.creation_preflight_context import (
        get_creation_preflight,
    )
    from aethos_core.providers.railway.deployment_plan.deployment_plan_context import (
        get_deployment_plan_context,
    )
    from aethos_core.providers.railway.service_creation_simulator.simulator_context import get_simulation

    plan = get_deployment_plan_context(session_id=session_id) or plan
    preflight = get_creation_preflight(session_id=session_id) or preflight
    simulation = get_simulation(session_id=session_id) or simulation
    return lifecycle, plan, preflight, simulation


def _needs_repair(
    *,
    plan: dict[str, Any] | None,
    preflight: dict[str, Any] | None,
    simulation: dict[str, Any] | None,
    require_plan: bool,
    require_preflight: bool,
    require_simulation: bool,
) -> bool:
    if not _global_index_can_hydrate():
        return False
    if require_plan and not (plan and plan.get("repo")):
        materializable, diag = load_best_global_lifecycle_record()
        if materializable:
            return True
        if diag.get("reason") == "readiness_only_no_plan":
            return False
        return bool(diag.get("reason"))
    if require_preflight and not (preflight and preflight.get("preflight_id")):
        return True
    if require_simulation and not (simulation and simulation.get("simulation_id")):
        return True
    return False


def _compute_ensure_result(
    *,
    plan: dict[str, Any] | None,
    preflight: dict[str, Any] | None,
    simulation: dict[str, Any] | None,
    require_plan: bool,
    require_preflight: bool,
    require_simulation: bool,
) -> str:
    has_plan = bool(plan and plan.get("repo"))
    has_preflight = bool(preflight and preflight.get("preflight_id"))
    has_simulation = bool(simulation and simulation.get("simulation_id"))

    if require_plan and not has_plan:
        return "miss"
    if require_preflight and not has_preflight:
        return "partial" if has_plan else "miss"
    if require_simulation and not has_simulation:
        return "partial" if has_plan or has_preflight else "miss"
    if has_plan or has_preflight or has_simulation:
        return "hit"
    return "miss"


def ensure_railway_deployment_lifecycle_for_lane(
    *,
    session_id: str,
    user_text: str = "",
    require_plan: bool = False,
    require_preflight: bool = False,
    require_simulation: bool = False,
) -> LifecycleLaneState:
    """Resolve lifecycle, repair from global index, materialize into session, and re-read artifacts."""
    from aethos_core.providers.railway.deployment_plan.deployment_plan_context import (
        get_deployment_plan_context,
    )

    session_id = (session_id or "default").strip()
    session_had_lifecycle = session_lifecycle_file_exists(session_id=session_id)
    session_had_plan = get_deployment_plan_context(session_id=session_id) is not None
    materialization_failure: dict[str, Any] = {}

    lifecycle = resolve_railway_deployment_lifecycle(session_id=session_id, user_text=user_text)
    lifecycle, plan, preflight, simulation = _materialize_and_reread(session_id=session_id, lifecycle=lifecycle)

    hydrated_from_global = bool(
        plan
        and _global_index_can_hydrate()
        and (not session_had_lifecycle or not session_had_plan)
    )

    if _needs_repair(
        plan=plan,
        preflight=preflight,
        simulation=simulation,
        require_plan=require_plan,
        require_preflight=require_preflight,
        require_simulation=require_simulation,
    ):
        materialized = force_materialize_latest_global_lifecycle(session_id=session_id)
        if materialized.get("ok"):
            lifecycle = materialized.get("lifecycle") or get_lifecycle_session(session_id=session_id) or lifecycle
            lifecycle, plan, preflight, simulation = _materialize_and_reread(
                session_id=session_id,
                lifecycle=lifecycle,
            )
            hydrated_from_global = True
        else:
            materialization_failure = dict(materialized)
            repair = repair_railway_deployment_lifecycle(session_id=session_id)
            if repair.get("ok"):
                lifecycle = repair.get("lifecycle") or get_lifecycle_session(session_id=session_id) or lifecycle
                lifecycle, plan, preflight, simulation = _materialize_and_reread(
                    session_id=session_id,
                    lifecycle=lifecycle,
                )
                hydrated_from_global = True

    ensure_result = _compute_ensure_result(
        plan=plan,
        preflight=preflight,
        simulation=simulation,
        require_plan=require_plan,
        require_preflight=require_preflight,
        require_simulation=require_simulation,
    )

    if plan and _global_index_can_hydrate() and (not session_had_plan or not session_had_lifecycle):
        hydrated_from_global = True

    return LifecycleLaneState(
        lifecycle=lifecycle,
        plan=plan,
        preflight=preflight,
        simulation=simulation,
        hydrated_from_global=hydrated_from_global,
        hydration_notice=_HYDRATION_NOTICE if hydrated_from_global else None,
        ensure_called=True,
        ensure_result=ensure_result,
        materialization_failure=materialization_failure,
    )


def is_fresh_runtime_lifecycle_state() -> bool:
    """True only when no global lifecycle index exists or it has zero entries."""
    from aethos_core.providers.railway.deployment_lifecycle.deployment_lifecycle_materialization import (
        global_lifecycle_index_has_entries,
    )

    if global_lifecycle_index_has_entries():
        return False
    index = inspect_global_lifecycle_index()
    if not index.get("exists"):
        return True
    return int(index.get("entries") or 0) < 1


def compose_fresh_runtime_lifecycle_reply() -> str:
    index = inspect_global_lifecycle_index()
    index_exists = bool(index.get("exists"))
    readable = bool(index.get("readable"))
    entries = int(index.get("entries") or 0)
    index_label = "present" if index_exists else "missing"
    readable_label = "yes" if readable else "no"
    return "\n".join(
        [
            "I don't have a Railway deployment lifecycle in this runtime yet.",
            "",
            "This appears to be a fresh runtime state:",
            f"- global lifecycle index: **{index_label}**",
            f"- lifecycle entries: **{entries}**",
            f"- global lifecycle readable: **{readable_label}**",
            "",
            "To create one, run:",
            "1. `create railway deployment plan for pilotmain/aethos in pilotos / production`",
            "2. `complete the railway deployment plan`",
            "3. `review railway deployment plan`",
            "4. `confirm railway deployment plan`",
            "5. `create railway service creation preflight`",
            "6. `simulate railway service creation`",
            "",
            "No mutation has been performed.",
        ]
    )


def compose_session_lifecycle_materialization_failed_reply(
    *,
    ensure_result: str = "miss",
    materialization: dict[str, Any] | None = None,
) -> str:
    from aethos_core.providers.railway.deployment_lifecycle.deployment_lifecycle_materialization import (
        global_lifecycle_index_has_entries,
    )

    index = inspect_global_lifecycle_index()
    entries = inspect_all_global_lifecycle_entries()
    if global_lifecycle_index_has_entries():
        lines = [
            "Railway deployment lifecycle index exists, but no usable deployment plan could be materialized.",
            "",
            "This indicates one of:",
            "- index entry points to a missing lifecycle file",
            "- lifecycle file is unreadable/corrupt",
            "- lifecycle record has no plan snapshot",
            "- data directory changed",
            "- session materialization failed",
            "",
            f"- Lifecycle ensure result: **{ensure_result}**",
            f"- Global lifecycle index exists: **yes**",
            f"- Global lifecycle entries: **{index.get('entries', 0)}**",
            f"- Global lifecycle readable: **{'yes' if index.get('readable') else 'no'}**",
        ]
    else:
        lines = [
            "I could not load a Railway deployment plan into this session.",
            "",
            "Global lifecycle data exists, but materialization into this session failed.",
            "",
            f"- Lifecycle ensure result: **{ensure_result}**",
            f"- Global lifecycle index exists: **{'yes' if index.get('exists') else 'no'}**",
            f"- Global lifecycle entries: **{index.get('entries', 0)}**",
            f"- Global lifecycle readable: **{'yes' if index.get('readable') else 'no'}**",
        ]
    if index.get("error"):
        lines.append(f"- Index error: {index['error']}")
    if materialization:
        reason = str(materialization.get("reason") or "").strip()
        detail = str(materialization.get("detail") or "").strip()
        if reason:
            lines.append(f"- Materialization failure: **{reason}**")
        if detail:
            lines.append(f"- Detail: {detail}")
    lines.append("")
    if entries:
        lines.extend(format_global_lifecycle_entry_lines(entries))
    reason = str((materialization or {}).get("reason") or "")
    if reason == "stale_index":
        lines.extend(
            [
                "Lifecycle index entry exists, but lifecycle file is missing. This index is stale.",
                "",
                "Try:",
                "`clear stale railway lifecycle index`",
                "or recreate the deployment lifecycle.",
            ]
        )
    elif reason == "readiness_only_no_plan":
        lines.extend(
            [
                "Readiness exists, but no deployment plan has been created yet.",
                "",
                "Try:",
                "`create railway deployment plan for <repo> in <project> / <environment>`",
            ]
        )
    elif reason == "plan_snapshot_missing":
        lines.extend(
            [
                "Lifecycle record exists but does not contain a deployment plan snapshot.",
                "",
                "Try:",
                "`create railway deployment plan for <repo> in <project> / <environment>`",
                "`confirm railway deployment plan`",
            ]
        )
    else:
        lines.extend(
            [
                "Try:",
                "`repair railway deployment lifecycle`",
                "`show railway deployment lifecycle`",
            ]
        )
    lines.extend(["", "No mutation has been performed."])
    return "\n".join(lines)


def compose_no_plan_after_lifecycle_ensure(
    *,
    ensure_result: str,
    session_id: str = "default",
    materialization_failure: dict[str, Any] | None = None,
    for_simulator: bool = False,
) -> str:
    if is_fresh_runtime_lifecycle_state():
        return compose_fresh_runtime_lifecycle_reply()

    session_lifecycle = get_lifecycle_session(session_id=session_id)
    if is_readiness_only_lifecycle(session_lifecycle):
        return compose_readiness_only_no_plan_reply(
            lifecycle=session_lifecycle,
            for_simulator=for_simulator,
        )

    materialization = materialization_failure
    if materialization:
        reason = str(materialization.get("reason") or "")
        if reason == "readiness_only_no_plan":
            rec = materialization.get("readiness_record") or materialization.get("lifecycle")
            return compose_readiness_only_no_plan_reply(
                lifecycle=rec if isinstance(rec, dict) else session_lifecycle,
                for_simulator=for_simulator,
            )
        if reason == "plan_snapshot_missing":
            entries = list(materialization.get("entries") or [])
            loaded = [e for e in entries if e.get("record_loaded")]
            if loaded and all(e.get("materialization_status") == "readiness_only" for e in loaded):
                return compose_readiness_only_no_plan_reply(
                    lifecycle=session_lifecycle,
                    for_simulator=for_simulator,
                )

    if not materialization and not is_fresh_runtime_lifecycle_state():
        _record, preload_diag = load_best_global_lifecycle_record()
        if preload_diag.get("reason") == "readiness_only_no_plan":
            rec = preload_diag.get("readiness_record")
            if isinstance(rec, dict):
                materialize_readiness_only_to_session(session_id=session_id, lifecycle=rec)
            return compose_readiness_only_no_plan_reply(
                lifecycle=rec if isinstance(rec, dict) else session_lifecycle,
                for_simulator=for_simulator,
            )
        materialization = force_materialize_latest_global_lifecycle(session_id=session_id)
        if materialization.get("ok"):
            from aethos_core.providers.railway.deployment_plan.deployment_plan_context import (
                get_deployment_plan_context,
            )

            if get_deployment_plan_context(session_id=session_id):
                return (
                    "Hydrated Railway deployment lifecycle from global index into this session.\n\n"
                    "Run:\n`show railway deployment plan`\n\n"
                    "No mutation has been performed."
                )
        if materialization.get("reason") == "readiness_only_no_plan":
            rec = materialization.get("readiness_record") or get_lifecycle_session(session_id=session_id)
            return compose_readiness_only_no_plan_reply(
                lifecycle=rec if isinstance(rec, dict) else None,
                for_simulator=for_simulator,
            )
    return compose_session_lifecycle_materialization_failed_reply(
        ensure_result=ensure_result,
        materialization=materialization,
    )


def prepend_hydration_notice(body: str, *, notice: str | None) -> str:
    if not notice:
        return body
    if notice in body:
        return body
    return f"{notice}\n\n{body}"

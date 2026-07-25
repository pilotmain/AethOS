# SPDX-License-Identifier: Apache-2.0
"""Route Railway service creation execution simulation (dry-run only)."""

from __future__ import annotations

from typing import Any

_BLOCKED_HANDLERS = (
    "generic_devops,explicit_mutation,railway_restart,github_workflow_lane,"
    "browser_observation,railway_mutation_preflight"
)


def route_railway_service_creation_simulator(
    text: str,
    *,
    session_id: str = "default",
) -> tuple[str, str, dict[str, str]] | None:
    from aethos_core.providers.railway.deployment_lifecycle.deployment_lifecycle_session_hydration import (
        LifecycleLaneState,
        compose_no_plan_after_lifecycle_ensure,
        ensure_railway_deployment_lifecycle_for_lane,
        prepend_hydration_notice,
    )
    from aethos_core.providers.railway.deployment_plan.deployment_plan_lifecycle import (
        classify_deployment_plan_lifecycle_state,
        compose_missing_preflight_reply,
        compose_unconfirmed_plan_reply,
    )
    from aethos_core.providers.railway.service_creation_simulator.simulator_context import (
        _without_repair_trace,
        get_simulation,
        save_simulation,
    )
    from aethos_core.providers.railway.execution_contract.execution_readiness_gate import (
        is_railway_execution_readiness_gate_intent,
    )
    from aethos_core.providers.railway.execution_contract.execution_router import (
        route_railway_execution_contract,
    )
    from aethos_core.providers.railway.service_creation_simulator.simulator_intent import (
        is_railway_service_creation_simulator_blocking_intent,
        is_railway_service_creation_simulator_failed_intent,
        is_railway_service_creation_simulator_intent,
        is_railway_service_creation_simulator_passed_intent,
        is_railway_service_creation_simulator_run_intent,
        is_railway_service_creation_simulator_show_intent,
    )

    raw = (text or "").strip()
    from aethos_core.providers.railway.execution_contract.execution_dry_run_executor import (
        parse_simulated_failure_phase,
    )

    if parse_simulated_failure_phase(raw):
        delegated = route_railway_execution_contract(raw, session_id=session_id)
        if delegated is not None:
            return delegated
    if is_railway_execution_readiness_gate_intent(raw):
        delegated = route_railway_execution_contract(raw, session_id=session_id)
        if delegated is not None:
            return delegated
    from aethos_core.providers.railway.service_creation_simulator.simulator_normalization import (
        normalize_simulation_snapshot,
    )
    from aethos_core.providers.railway.service_creation_simulator.simulator_renderer import (
        render_blocking_followup,
        render_failed_followup,
        render_passed_followup,
        render_simulation_artifact,
    )
    from aethos_core.providers.railway.service_creation_simulator.simulator_result import (
        build_simulation_result,
    )

    raw = (text or "").strip()
    if not is_railway_service_creation_simulator_intent(raw):
        return None

    lane = ensure_railway_deployment_lifecycle_for_lane(
        session_id=session_id,
        user_text=raw,
        require_plan=True,
        require_preflight=False,
        require_simulation=False,
    )
    plan = lane.plan
    preflight = lane.preflight

    normalized_stale_credential_blocker = False

    def _ensure_lane(
        *,
        require_plan: bool = True,
        require_preflight: bool = False,
        require_simulation: bool = False,
    ) -> LifecycleLaneState:
        return ensure_railway_deployment_lifecycle_for_lane(
            session_id=session_id,
            user_text=raw,
            require_plan=require_plan,
            require_preflight=require_preflight,
            require_simulation=require_simulation,
        )

    def _load_saved_simulation(*, follow_lane: LifecycleLaneState | None = None) -> dict[str, Any] | None:
        nonlocal normalized_stale_credential_blocker
        source_lane = follow_lane or lane
        saved_local = get_simulation(session_id=session_id) or source_lane.simulation
        if not saved_local:
            return None
        repaired_this_turn = bool(saved_local.pop("normalized_stale_credential_blocker_repaired", False))
        saved_local, repaired_now = normalize_simulation_snapshot(dict(saved_local))
        normalized_stale_credential_blocker = normalized_stale_credential_blocker or repaired_this_turn or repaired_now
        if normalized_stale_credential_blocker:
            save_simulation(session_id=session_id, simulation=_without_repair_trace(saved_local))
        return saved_local

    def _try_build_simulation_from_lane(source_lane: LifecycleLaneState) -> dict[str, Any] | None:
        if not source_lane.plan or not source_lane.preflight:
            return None
        if classify_deployment_plan_lifecycle_state(source_lane.plan) != "confirmed_ready":
            return None
        simulation = build_simulation_result(
            plan=source_lane.plan,
            preflight=source_lane.preflight,
            session_id=session_id,
        )
        save_simulation(session_id=session_id, simulation=simulation)
        return simulation

    def _lifecycle_blocker_reply(
        source_lane: LifecycleLaneState,
    ) -> tuple[str, str, dict[str, str]] | None:
        state = classify_deployment_plan_lifecycle_state(source_lane.plan)
        if state == "no_plan":
            return (
                compose_no_plan_after_lifecycle_ensure(
                    ensure_result=source_lane.ensure_result,
                    session_id=session_id,
                    materialization_failure=source_lane.materialization_failure,
                    for_simulator=True,
                ),
                "railway_service_creation_simulation_not_ready",
                _meta(source_lane, session_id=session_id, simulation={}, stage="not_ready"),
            )
        if state == "unconfirmed":
            return (
                compose_unconfirmed_plan_reply(plan=source_lane.plan or {}),
                "railway_service_creation_simulation_not_ready",
                _meta(source_lane, session_id=session_id, simulation={}, stage="not_ready"),
            )
        if not source_lane.preflight:
            return (
                compose_missing_preflight_reply(plan=source_lane.plan or {}),
                "railway_service_creation_simulation_not_ready",
                _meta(source_lane, session_id=session_id, simulation={}, stage="not_ready"),
            )
        return None

    def _merge_hydration(base_lane: LifecycleLaneState, follow_lane: LifecycleLaneState) -> LifecycleLaneState:
        from dataclasses import replace

        if not base_lane.hydrated_from_global:
            return follow_lane
        if follow_lane.hydrated_from_global:
            return follow_lane
        return replace(
            follow_lane,
            hydrated_from_global=True,
            hydration_notice=follow_lane.hydration_notice or base_lane.hydration_notice,
        )

    def _resolve_saved_simulation_for_followup() -> tuple[dict[str, Any] | None, LifecycleLaneState]:
        follow_lane = _merge_hydration(
            lane,
            _ensure_lane(require_plan=True, require_preflight=True, require_simulation=True),
        )
        saved_local = _load_saved_simulation(follow_lane=follow_lane)
        if saved_local:
            return saved_local, follow_lane
        built = _try_build_simulation_from_lane(follow_lane)
        if built:
            return _load_saved_simulation(follow_lane=follow_lane) or built, follow_lane
        return None, follow_lane

    def _finish(
        body: str,
        intent: str,
        *,
        source_lane: LifecycleLaneState,
        simulation: dict[str, Any],
        stage: str,
    ) -> tuple[str, str, dict[str, str]]:
        return (
            prepend_hydration_notice(body, notice=source_lane.hydration_notice),
            intent,
            _meta(
                source_lane,
                session_id=session_id,
                simulation=simulation,
                stage=stage,
                normalized_stale_credential_blocker=normalized_stale_credential_blocker,
            ),
        )

    if is_railway_service_creation_simulator_blocking_intent(raw):
        saved, follow_lane = _resolve_saved_simulation_for_followup()
        if not saved:
            blocked = _lifecycle_blocker_reply(follow_lane)
            if blocked is not None:
                return blocked
            return (
                "No saved Railway service creation simulation for this session.\n\n"
                "Run:\n`simulate railway service creation`\n\n"
                "No mutation has been performed.",
                "railway_service_creation_simulation_blocking_missing",
                _meta(follow_lane, session_id=session_id, simulation={}, stage="blocking_missing"),
            )
        return _finish(
            render_blocking_followup(saved),
            "railway_service_creation_simulation_blocking",
            source_lane=follow_lane,
            simulation=saved,
            stage="blocking_followup",
        )

    if is_railway_service_creation_simulator_passed_intent(raw):
        saved, follow_lane = _resolve_saved_simulation_for_followup()
        if not saved:
            blocked = _lifecycle_blocker_reply(follow_lane)
            if blocked is not None:
                return blocked
            return (
                "No saved simulation. Run `simulate railway service creation` first.",
                "railway_service_creation_simulation_passed_missing",
                _meta(follow_lane, session_id=session_id, simulation={}, stage="passed_missing"),
            )
        return _finish(
            render_passed_followup(saved),
            "railway_service_creation_simulation_passed",
            source_lane=follow_lane,
            simulation=saved,
            stage="passed_followup",
        )

    if is_railway_service_creation_simulator_failed_intent(raw):
        saved, follow_lane = _resolve_saved_simulation_for_followup()
        if not saved:
            blocked = _lifecycle_blocker_reply(follow_lane)
            if blocked is not None:
                return blocked
            return (
                "No saved simulation. Run `simulate railway service creation` first.",
                "railway_service_creation_simulation_failed_missing",
                _meta(follow_lane, session_id=session_id, simulation={}, stage="failed_missing"),
            )
        return _finish(
            render_failed_followup(saved),
            "railway_service_creation_simulation_failed",
            source_lane=follow_lane,
            simulation=saved,
            stage="failed_followup",
        )

    if is_railway_service_creation_simulator_show_intent(raw):
        saved, follow_lane = _resolve_saved_simulation_for_followup()
        if not saved:
            blocked = _lifecycle_blocker_reply(follow_lane)
            if blocked is not None:
                return blocked
            return (
                "No saved Railway service creation simulation.\n\n"
                "Run:\n`simulate railway service creation`\n\n"
                "No mutation has been performed.",
                "railway_service_creation_simulation_show_missing",
                _meta(follow_lane, session_id=session_id, simulation={}, stage="show_missing"),
            )
        return _finish(
            render_simulation_artifact(saved, session_id=session_id),
            "railway_service_creation_simulation_show",
            source_lane=follow_lane,
            simulation=saved,
            stage="show_simulation",
        )

    if is_railway_service_creation_simulator_run_intent(raw):
        run_lane = _merge_hydration(
            lane,
            _ensure_lane(require_plan=True, require_preflight=True, require_simulation=False),
        )
        blocked = _lifecycle_blocker_reply(run_lane)
        if blocked is not None:
            return blocked
        simulation = build_simulation_result(
            plan=run_lane.plan or {},
            preflight=run_lane.preflight or {},
            session_id=session_id,
        )
        save_simulation(session_id=session_id, simulation=simulation)
        return _finish(
            render_simulation_artifact(simulation, session_id=session_id),
            "railway_service_creation_simulation",
            source_lane=run_lane,
            simulation=simulation,
            stage="simulation_complete",
        )

    return None


def _meta(
    lane: Any,
    *,
    session_id: str,
    simulation: dict[str, Any],
    stage: str,
    normalized_stale_credential_blocker: bool = False,
) -> dict[str, str]:
    meta = {
        "route_id": "railway_service_creation_simulator",
        "matched_module": "providers.railway.service_creation_simulator.simulator_router",
        "railway_service_creation_simulation_stage": stage,
        "blocked_handlers": _BLOCKED_HANDLERS,
        "session_id": session_id,
        "readonly": "true",
        "mutation_performed": "false",
        "execution_enabled": "false",
        "presentation_bypass": "true",
        "presentation_mode": "engineering",
        "suppress_governance_footer": "true",
        "lifecycle_ensure_called": "true",
        "lifecycle_ensure_result": str(getattr(lane, "ensure_result", "miss") or "miss"),
    }
    if getattr(lane, "ensure_called", True):
        meta["lifecycle_ensure_called"] = "true"
    if getattr(lane, "hydrated_from_global", False):
        meta["hydrated_from_global_lifecycle"] = "true"
    if simulation.get("simulation_id"):
        meta["simulation_id"] = str(simulation["simulation_id"])
    if simulation.get("repo"):
        meta["repo"] = str(simulation["repo"])
    meta["ready_to_execute"] = "true" if simulation.get("ready_to_execute") else "false"
    if simulation.get("blocking_reasons"):
        meta["blocking_reasons"] = ",".join(str(c) for c in simulation["blocking_reasons"])
    if normalized_stale_credential_blocker:
        meta["normalized_stale_credential_blocker"] = "true"
    return meta

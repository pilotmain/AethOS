# SPDX-License-Identifier: Apache-2.0
"""Route Railway new-service creation preflight — governed artifact only."""

from __future__ import annotations

from typing import Any

_BLOCKED_HANDLERS = (
    "front_door,devops_capability,github_workflow_lane,explicit_mutation,"
    "railway_mutation_preflight,generic_help,browser_observation"
)


def route_railway_service_creation_preflight(
    text: str,
    *,
    session_id: str = "default",
) -> tuple[str, str, dict[str, str]] | None:
    from aethos_core.providers.railway.deployment_plan.creation_preflight import (
        apply_preflight_approval,
        build_creation_preflight_from_plan,
        compose_creation_preflight_artifact,
        plan_eligible_for_creation_preflight,
    )
    from aethos_core.providers.railway.deployment_plan.creation_preflight_context import (
        get_creation_preflight,
        save_creation_preflight,
    )
    from aethos_core.providers.railway.deployment_plan.creation_preflight_intent import (
        is_railway_service_creation_preflight_approve_intent,
        is_railway_service_creation_preflight_create_intent,
        is_railway_service_creation_preflight_intent,
        is_railway_service_creation_preflight_show_intent,
    )
    from aethos_core.providers.railway.deployment_lifecycle.deployment_lifecycle_session_hydration import (
        ensure_railway_deployment_lifecycle_for_lane,
        prepend_hydration_notice,
    )
    from aethos_core.providers.railway.deployment_lifecycle.deployment_lifecycle_session_hydration import (
        compose_no_plan_after_lifecycle_ensure,
    )
    from aethos_core.providers.railway.deployment_plan.deployment_plan_lifecycle import (
        classify_deployment_plan_lifecycle_state,
        compose_missing_preflight_reply,
        compose_preflight_not_ready_reply,
        compose_unconfirmed_plan_reply,
    )

    raw = (text or "").strip()
    if not is_railway_service_creation_preflight_intent(raw):
        return None

    lane = ensure_railway_deployment_lifecycle_for_lane(
        session_id=session_id,
        user_text=raw,
        require_plan=True,
        require_preflight=False,
        require_simulation=False,
    )
    plan = lane.plan
    existing_preflight = lane.preflight

    if is_railway_service_creation_preflight_approve_intent(raw):
        if not existing_preflight:
            return (
                "No Railway service creation preflight exists for this session.\n\n"
                "Create one first:\n"
                "`create railway service creation preflight`\n\n"
                "No mutation has been performed.",
                "railway_creation_preflight_approve_missing",
                _meta(session_id, stage="approve_missing", preflight={}),
            )
        if existing_preflight.get("preflight_approved"):
            body = compose_creation_preflight_artifact(existing_preflight)
            return body, "railway_creation_preflight_approve_already", _meta(
                session_id, stage="approve_already", preflight=existing_preflight
            )
        updated = apply_preflight_approval(existing_preflight)
        save_creation_preflight(session_id=session_id, preflight=updated)
        body = compose_creation_preflight_artifact(updated)
        return body, "railway_creation_preflight_approved", _meta(
            session_id, stage="preflight_approved", preflight=updated
        )

    if is_railway_service_creation_preflight_show_intent(raw):
        if not existing_preflight:
            return (
                "No saved Railway service creation preflight for this session.\n\n"
                "Create one first:\n"
                "`create railway service creation preflight`\n\n"
                "No mutation has been performed.",
                "railway_creation_preflight_show_missing",
                _meta(session_id, stage="show_missing", preflight={}),
            )
        body = compose_creation_preflight_artifact(existing_preflight)
        return body, "railway_creation_preflight_show", _meta(
            session_id, stage="show_preflight", preflight=existing_preflight
        )

    if is_railway_service_creation_preflight_create_intent(raw):
        state = classify_deployment_plan_lifecycle_state(plan)
        if state == "no_plan":
            return (
                compose_no_plan_after_lifecycle_ensure(
                    ensure_result=lane.ensure_result,
                    session_id=session_id,
                    materialization_failure=lane.materialization_failure,
                ),
                "railway_creation_preflight_not_ready",
                _meta(session_id, stage="not_ready", preflight={}, hydrated_from_global=lane.hydrated_from_global),
            )
        if state == "unconfirmed":
            return (
                compose_unconfirmed_plan_reply(plan=plan or {}),
                "railway_creation_preflight_not_ready",
                _meta(session_id, stage="not_ready", preflight={}),
            )
        eligible, blockers = plan_eligible_for_creation_preflight(plan or {})
        if not eligible:
            return (
                compose_preflight_not_ready_reply(blockers=blockers),
                "railway_creation_preflight_not_ready",
                _meta(session_id, stage="not_ready", preflight={}),
            )
        preflight = build_creation_preflight_from_plan(plan or {})
        save_creation_preflight(session_id=session_id, preflight=preflight)
        body = prepend_hydration_notice(
            compose_creation_preflight_artifact(preflight),
            notice=lane.hydration_notice,
        )
        return body, "railway_creation_preflight_draft", _meta(
            session_id,
            stage="preflight_draft",
            preflight=preflight,
            hydrated_from_global=lane.hydrated_from_global,
        )

    return None


def _meta(
    session_id: str,
    *,
    stage: str,
    preflight: dict[str, Any],
    hydrated_from_global: bool = False,
) -> dict[str, str]:
    meta = {
        "route_id": "railway_deployment_creation_preflight",
        "matched_module": "providers.railway.deployment_plan.creation_preflight_router",
        "railway_creation_preflight_stage": stage,
        "blocked_handlers": _BLOCKED_HANDLERS,
        "session_id": session_id,
        "readonly": "true",
        "mutation_performed": "false",
        "execution_enabled": "false",
        "presentation_bypass": "true",
        "presentation_mode": "engineering",
        "suppress_governance_footer": "true",
    }
    if preflight.get("preflight_id"):
        meta["preflight_id"] = str(preflight["preflight_id"])
    if preflight.get("repo"):
        meta["repo"] = str(preflight["repo"])
    meta["preflight_approved"] = "true" if preflight.get("preflight_approved") else "false"
    if hydrated_from_global:
        meta["hydrated_from_global_lifecycle"] = "true"
    return meta

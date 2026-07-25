# SPDX-License-Identifier: Apache-2.0
"""FIX 189 — chat router for bounded multi-agent delivery execution."""

from __future__ import annotations

from aethos_core.mission_control.bounded_multi_agent_delivery_execution.bounded_multi_agent_delivery_execution_contract import (
    AGENT_EXECUTION_AUTHORITY_FIX_189,
    BOUNDED_MULTI_AGENT_DELIVERY_EXECUTION_ROUTE_ID,
    DEPLOY_AUTHORITY_FIX_189,
    GATE_BYPASS_ENABLED_FIX_189,
    MERGE_AUTHORITY_FIX_189,
    MUTATION_PERFORMED_FIX_189,
    PROVIDER_AUTHORITY_FIX_189,
    RAILWAY_AUTHORITY_FIX_189,
)
from aethos_core.mission_control.bounded_multi_agent_delivery_execution.bounded_multi_agent_delivery_execution_intent import (
    is_bounded_multi_agent_delivery_execution_intent,
    parse_bounded_multi_agent_delivery_execution_record_intent,
    parse_run_bounded_agent_delivery_execution_intent,
)
from aethos_core.mission_control.bounded_multi_agent_delivery_execution.bounded_multi_agent_delivery_execution_renderer import (
    render_bounded_multi_agent_delivery_execution,
)
from aethos_core.mission_control.bounded_multi_agent_delivery_execution.bounded_multi_agent_delivery_execution_service import (
    build_bounded_multi_agent_delivery_execution,
    run_bounded_multi_agent_delivery_execution,
)
from aethos_core.mission_control.bounded_multi_agent_delivery_execution.bounded_multi_agent_delivery_execution_store import (
    append_bounded_multi_agent_delivery_execution_record,
)
from aethos_core.mission_control.mission_authorization.mission_authorization_service import (
    build_mission_authorization,
)


def _meta(session_id: str, *, stage: str, **extra: str) -> dict[str, str]:
    return {
        "route_id": BOUNDED_MULTI_AGENT_DELIVERY_EXECUTION_ROUTE_ID,
        "matched_module": (
            "mission_control.bounded_multi_agent_delivery_execution."
            "bounded_multi_agent_delivery_execution_router"
        ),
        "session_id": session_id,
        "readonly": "true",
        "mutation_performed": "false" if MUTATION_PERFORMED_FIX_189 is False else "true",
        "agent_execution_authority": "false" if AGENT_EXECUTION_AUTHORITY_FIX_189 is False else "true",
        "merge_authority": "false" if MERGE_AUTHORITY_FIX_189 is False else "true",
        "deploy_authority": "false" if DEPLOY_AUTHORITY_FIX_189 is False else "true",
        "railway_authority": "false" if RAILWAY_AUTHORITY_FIX_189 is False else "true",
        "provider_authority": "false" if PROVIDER_AUTHORITY_FIX_189 is False else "true",
        "gate_bypass_enabled": "false" if GATE_BYPASS_ENABLED_FIX_189 is False else "true",
        "mutation_scope": "bounded_multi_agent_delivery_execution",
        "presentation_bypass": "true",
        "presentation_mode": "engineering",
        "suppress_governance_footer": "true",
        "mission_control_stage": stage,
        "lane_separation": "agent_work_not_execution_authority",
        **extra,
    }


def route_bounded_multi_agent_delivery_execution(
    text: str,
    *,
    session_id: str = "default",
) -> tuple[str, str, dict[str, str]] | None:
    run_role = parse_run_bounded_agent_delivery_execution_intent(text)
    if run_role is not None:
        outcome = run_bounded_multi_agent_delivery_execution(session_id=session_id, role_id=run_role)
        roles = ", ".join(str(o.get("agent_role_id")) for o in outcome.agent_outputs) or run_role
        body = (
            f"Bounded agent delivery execution routed {len(outcome.agent_outputs)} package(s) "
            f"({roles}). Pipeline state: {outcome.pipeline_state}. "
            f"Agent execution authority remains false."
        )
        if not outcome.ok:
            body = f"Partial/blocked: {', '.join(outcome.blockers[:4])}. {body}"
        return (
            body,
            "mission_control_bounded_multi_agent_delivery_execution_run",
            _meta(
                session_id,
                stage="agent_execution_run",
                pipeline_state=outcome.pipeline_state,
                bounded_work_performed="true",
            ),
        )

    record_intent = parse_bounded_multi_agent_delivery_execution_record_intent(text)
    if record_intent is not None:
        kind, content = record_intent
        auth = build_mission_authorization(session_id=session_id)
        board = auth.mission_authorization if auth.ok else {}
        record, blockers = append_bounded_multi_agent_delivery_execution_record(
            session_id=session_id,
            kind=kind,
            content=content,
            plan_id=str(board.get("plan_id") or "") or None,
            correlation_id=str(board.get("correlation_id") or "") or None,
        )
        if blockers or not record:
            body = f"Agent execution record blocked: {', '.join(blockers)}"
            return (
                body,
                "mission_control_bounded_multi_agent_delivery_execution_record_blocked",
                _meta(session_id, stage="blocked"),
            )
        body = (
            f"Agent execution record persisted (`{record.get('record_id')}`, kind `{kind}`). "
            "Agents perform work — gates decide."
        )
        return (
            body,
            "mission_control_bounded_multi_agent_delivery_execution_record",
            _meta(session_id, stage="agent_execution_record", record_id=str(record.get("record_id") or "")),
        )

    if not is_bounded_multi_agent_delivery_execution_intent(text):
        return None

    result = build_bounded_multi_agent_delivery_execution(session_id=session_id)
    body = render_bounded_multi_agent_delivery_execution(result.bounded_multi_agent_delivery_execution)
    return (
        body,
        "mission_control_bounded_multi_agent_delivery_execution",
        _meta(
            session_id,
            stage="bounded_multi_agent_delivery_execution",
            pipeline_state=str(result.bounded_multi_agent_delivery_execution.get("pipeline_state") or ""),
        ),
    )

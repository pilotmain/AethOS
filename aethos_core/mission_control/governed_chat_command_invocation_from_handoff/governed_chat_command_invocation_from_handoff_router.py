# SPDX-License-Identifier: Apache-2.0
"""FIX 180 — chat router for governed chat command invocation from handoff."""

from __future__ import annotations

from aethos_core.mission_control.governed_chat_command_invocation_from_handoff.governed_chat_command_invocation_from_handoff_contract import (
    AUTONOMOUS_EXECUTION_ENABLED_FIX_180,
    AUTONOMOUS_LANE_ENTRY_ENABLED_FIX_180,
    DIRECT_EXECUTION_PERFORMED_FIX_180,
    DIRECT_PROVIDER_MUTATION_PERFORMED_FIX_180,
    EXECUTION_PERFORMED_FIX_180,
    GATE_BYPASS_ENABLED_FIX_180,
    GOVERNED_CHAT_COMMAND_INVOCATION_FROM_HANDOFF_ROUTE_ID,
    HIDDEN_COMMAND_EXECUTION_PERFORMED_FIX_180,
    LANE_ADMISSION_EXECUTED_FIX_180,
    LANE_ENTRY_EXECUTION_PERFORMED_FIX_180,
    MUTATION_PERFORMED_FIX_180,
)
from aethos_core.mission_control.governed_chat_command_invocation_from_handoff.governed_chat_command_invocation_from_handoff_intent import (
    is_governed_chat_command_invocation_from_handoff_intent,
    is_invoke_handoff_command_intent,
    parse_governed_chat_command_invocation_from_handoff_record_intent,
)
from aethos_core.mission_control.governed_chat_command_invocation_from_handoff.governed_chat_command_invocation_from_handoff_renderer import (
    render_governed_chat_command_invocation_from_handoff,
)
from aethos_core.mission_control.governed_chat_command_invocation_from_handoff.governed_chat_command_invocation_from_handoff_service import (
    build_governed_chat_command_invocation_from_handoff,
    invoke_governed_chat_command_from_handoff,
)
from aethos_core.mission_control.governed_chat_command_invocation_from_handoff.governed_chat_command_invocation_from_handoff_store import (
    append_governed_chat_command_invocation_from_handoff_record,
)
from aethos_core.mission_control.frozen_gate_execution_request_adapter.frozen_gate_execution_request_adapter_service import (
    build_frozen_gate_execution_request_adapter,
)


def _meta(session_id: str, *, stage: str, **extra: str) -> dict[str, str]:
    return {
        "route_id": GOVERNED_CHAT_COMMAND_INVOCATION_FROM_HANDOFF_ROUTE_ID,
        "matched_module": "mission_control.governed_chat_command_invocation_from_handoff.governed_chat_command_invocation_from_handoff_router",
        "session_id": session_id,
        "readonly": "true",
        "mutation_performed": "false" if MUTATION_PERFORMED_FIX_180 is False else "true",
        "execution_performed": "false" if EXECUTION_PERFORMED_FIX_180 is False else "true",
        "direct_execution_performed": "false" if DIRECT_EXECUTION_PERFORMED_FIX_180 is False else "true",
        "direct_provider_mutation_performed": "false"
        if DIRECT_PROVIDER_MUTATION_PERFORMED_FIX_180 is False
        else "true",
        "hidden_command_execution_performed": "false"
        if HIDDEN_COMMAND_EXECUTION_PERFORMED_FIX_180 is False
        else "true",
        "lane_entry_execution_performed": "false" if LANE_ENTRY_EXECUTION_PERFORMED_FIX_180 is False else "true",
        "lane_admission_executed": "false" if LANE_ADMISSION_EXECUTED_FIX_180 is False else "true",
        "autonomous_execution_enabled": "false" if AUTONOMOUS_EXECUTION_ENABLED_FIX_180 is False else "true",
        "autonomous_lane_entry_enabled": "false" if AUTONOMOUS_LANE_ENTRY_ENABLED_FIX_180 is False else "true",
        "gate_bypass_enabled": "false" if GATE_BYPASS_ENABLED_FIX_180 is False else "true",
        "mutation_scope": "governed_chat_command_invocation_from_handoff_memory_only",
        "presentation_bypass": "true",
        "presentation_mode": "engineering",
        "suppress_governance_footer": "true",
        "mission_control_stage": stage,
        "lane_separation": "handoff_invocation_not_direct_execution",
        **extra,
    }


def route_governed_chat_command_invocation_from_handoff(
    text: str,
    *,
    session_id: str = "default",
) -> tuple[str, str, dict[str, str]] | None:
    if is_invoke_handoff_command_intent(text):
        outcome = invoke_governed_chat_command_from_handoff(session_id=session_id)
        if not outcome.ok:
            body = f"Handoff command invocation blocked: {', '.join(outcome.blockers)}"
            return (
                body,
                "mission_control_governed_chat_command_invocation_from_handoff_invoke_blocked",
                _meta(session_id, stage="blocked"),
            )
        body = (
            f"Handoff command invoked through chat governance (`{outcome.route_id or 'route_unknown'}`). "
            f"Audit `{outcome.audit_id}`. Direct provider mutation: false.\n\n{outcome.reply}"
        )
        return (
            body,
            "mission_control_governed_chat_command_invocation_from_handoff_invoke",
            _meta(
                session_id,
                stage="governed_chat_command_invocation_invoke",
                audit_id=outcome.audit_id,
                chat_route_id=outcome.route_id,
                chat_governance_routed="true",
                direct_provider_mutation_performed="false",
                handoff_invocation_origin_logged="true",
            ),
        )

    record_intent = parse_governed_chat_command_invocation_from_handoff_record_intent(text)
    if record_intent is not None:
        kind, content = record_intent
        adapter = build_frozen_gate_execution_request_adapter(session_id=session_id)
        ctx = adapter.frozen_gate_execution_request_adapter if adapter.ok else {}
        record, blockers = append_governed_chat_command_invocation_from_handoff_record(
            session_id=session_id,
            kind=kind,
            content=content,
            plan_id=str(ctx.get("plan_id") or "") or None,
            correlation_id=str(ctx.get("correlation_id") or "") or None,
        )
        if blockers or not record:
            body = f"Governed chat command invocation record blocked: {', '.join(blockers)}"
            return (
                body,
                "mission_control_governed_chat_command_invocation_from_handoff_record_blocked",
                _meta(session_id, stage="blocked"),
            )
        body = (
            f"Handoff invocation record persisted (`{record.get('record_id')}`, kind `{kind}`). "
            "Use `invoke handoff command` to route through chat governance."
        )
        return (
            body,
            "mission_control_governed_chat_command_invocation_from_handoff_record",
            _meta(
                session_id,
                stage="governed_chat_command_invocation_record",
                record_id=str(record.get("record_id") or ""),
                governed_chat_command_invocation_from_handoff_memory_only="true",
            ),
        )

    if not is_governed_chat_command_invocation_from_handoff_intent(text):
        return None

    result = build_governed_chat_command_invocation_from_handoff(session_id=session_id)
    if not result.ok:
        body = f"Governed chat command invocation unavailable: {', '.join(result.blockers)}"
        return (
            body,
            "mission_control_governed_chat_command_invocation_from_handoff_blocked",
            _meta(session_id, stage="blocked"),
        )

    body = render_governed_chat_command_invocation_from_handoff(
        result.governed_chat_command_invocation_from_handoff
    )
    return (
        body,
        "mission_control_governed_chat_command_invocation_from_handoff",
        _meta(
            session_id,
            stage="governed_chat_command_invocation_from_handoff",
            invocation_record_count=str(
                result.governed_chat_command_invocation_from_handoff.get("invocation_record_count", 0)
            ),
        ),
    )

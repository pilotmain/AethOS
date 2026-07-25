# SPDX-License-Identifier: Apache-2.0
"""FIX 179 — chat router for frozen gate execution request adapter."""

from __future__ import annotations

from aethos_core.mission_control.frozen_gate_execution_request_adapter.frozen_gate_execution_request_adapter_contract import (
    AUTONOMOUS_EXECUTION_ENABLED_FIX_179,
    AUTONOMOUS_LANE_ENTRY_ENABLED_FIX_179,
    COMMAND_EXECUTION_PERFORMED_FIX_179,
    EXECUTION_PERFORMED_FIX_179,
    FROZEN_GATE_EXECUTION_REQUEST_ADAPTER_ROUTE_ID,
    GATE_BYPASS_ENABLED_FIX_179,
    GATE_EXECUTION_PERFORMED_FIX_179,
    LANE_ADMISSION_EXECUTED_FIX_179,
    LANE_ENTRY_EXECUTION_PERFORMED_FIX_179,
    MUTATION_PERFORMED_FIX_179,
)
from aethos_core.mission_control.frozen_gate_execution_request_adapter.frozen_gate_execution_request_adapter_intent import (
    is_frozen_gate_execution_request_adapter_intent,
    parse_frozen_gate_execution_request_adapter_record_intent,
)
from aethos_core.mission_control.frozen_gate_execution_request_adapter.frozen_gate_execution_request_adapter_renderer import (
    render_frozen_gate_execution_request_adapter,
)
from aethos_core.mission_control.frozen_gate_execution_request_adapter.frozen_gate_execution_request_adapter_service import (
    build_frozen_gate_execution_request_adapter,
)
from aethos_core.mission_control.frozen_gate_execution_request_adapter.frozen_gate_execution_request_adapter_store import (
    append_frozen_gate_execution_request_adapter_record,
)
from aethos_core.mission_control.frozen_gate_intake_preview.frozen_gate_intake_preview_service import (
    build_frozen_gate_intake_preview,
)


def _meta(session_id: str, *, stage: str, **extra: str) -> dict[str, str]:
    return {
        "route_id": FROZEN_GATE_EXECUTION_REQUEST_ADAPTER_ROUTE_ID,
        "matched_module": "mission_control.frozen_gate_execution_request_adapter.frozen_gate_execution_request_adapter_router",
        "session_id": session_id,
        "readonly": "true",
        "mutation_performed": "false" if MUTATION_PERFORMED_FIX_179 is False else "true",
        "execution_performed": "false" if EXECUTION_PERFORMED_FIX_179 is False else "true",
        "command_execution_performed": "false" if COMMAND_EXECUTION_PERFORMED_FIX_179 is False else "true",
        "gate_execution_performed": "false" if GATE_EXECUTION_PERFORMED_FIX_179 is False else "true",
        "lane_entry_execution_performed": "false" if LANE_ENTRY_EXECUTION_PERFORMED_FIX_179 is False else "true",
        "lane_admission_executed": "false" if LANE_ADMISSION_EXECUTED_FIX_179 is False else "true",
        "autonomous_execution_enabled": "false" if AUTONOMOUS_EXECUTION_ENABLED_FIX_179 is False else "true",
        "autonomous_lane_entry_enabled": "false" if AUTONOMOUS_LANE_ENTRY_ENABLED_FIX_179 is False else "true",
        "gate_bypass_enabled": "false" if GATE_BYPASS_ENABLED_FIX_179 is False else "true",
        "mutation_scope": "frozen_gate_execution_request_adapter_memory_only",
        "presentation_bypass": "true",
        "presentation_mode": "engineering",
        "suppress_governance_footer": "true",
        "mission_control_stage": stage,
        "lane_separation": "execution_request_not_command_execution",
        **extra,
    }


def route_frozen_gate_execution_request_adapter(
    text: str,
    *,
    session_id: str = "default",
) -> tuple[str, str, dict[str, str]] | None:
    record_intent = parse_frozen_gate_execution_request_adapter_record_intent(text)
    if record_intent is not None:
        kind, content = record_intent
        preview = build_frozen_gate_intake_preview(session_id=session_id)
        ctx = preview.frozen_gate_intake_preview if preview.ok else {}
        record, blockers = append_frozen_gate_execution_request_adapter_record(
            session_id=session_id,
            kind=kind,
            content=content,
            plan_id=str(ctx.get("plan_id") or "") or None,
            correlation_id=str(ctx.get("correlation_id") or "") or None,
        )
        if blockers or not record:
            body = f"Frozen gate execution request record blocked: {', '.join(blockers)}"
            return (
                body,
                "mission_control_frozen_gate_execution_request_adapter_record_blocked",
                _meta(session_id, stage="blocked"),
            )
        body = (
            f"Gate execution request record persisted (`{record.get('record_id')}`, kind `{kind}`). "
            "Request only — operator invokes frozen command via normal chat governance."
        )
        return (
            body,
            "mission_control_frozen_gate_execution_request_adapter_record",
            _meta(
                session_id,
                stage="frozen_gate_execution_request_adapter_record",
                record_id=str(record.get("record_id") or ""),
                frozen_gate_execution_request_adapter_memory_only="true",
            ),
        )

    if not is_frozen_gate_execution_request_adapter_intent(text):
        return None

    result = build_frozen_gate_execution_request_adapter(session_id=session_id)
    if not result.ok:
        body = f"Frozen gate execution request adapter unavailable: {', '.join(result.blockers)}"
        return (
            body,
            "mission_control_frozen_gate_execution_request_adapter_blocked",
            _meta(session_id, stage="blocked"),
        )

    body = render_frozen_gate_execution_request_adapter(result.frozen_gate_execution_request_adapter)
    return (
        body,
        "mission_control_frozen_gate_execution_request_adapter",
        _meta(
            session_id,
            stage="frozen_gate_execution_request_adapter",
            execution_request_record_count=str(
                result.frozen_gate_execution_request_adapter.get("execution_request_record_count", 0)
            ),
        ),
    )

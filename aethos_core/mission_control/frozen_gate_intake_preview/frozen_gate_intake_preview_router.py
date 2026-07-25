# SPDX-License-Identifier: Apache-2.0
"""FIX 178 — chat router for frozen gate intake preview."""

from __future__ import annotations

from aethos_core.mission_control.frozen_gate_intake_preview.frozen_gate_intake_preview_contract import (
    AUTONOMOUS_EXECUTION_ENABLED_FIX_178,
    AUTONOMOUS_LANE_ENTRY_ENABLED_FIX_178,
    EXECUTION_PERFORMED_FIX_178,
    FROZEN_GATE_INTAKE_PREVIEW_ROUTE_ID,
    GATE_BYPASS_ENABLED_FIX_178,
    GATE_EXECUTION_PERFORMED_FIX_178,
    LANE_ADMISSION_EXECUTED_FIX_178,
    LANE_ENTRY_EXECUTION_PERFORMED_FIX_178,
    MUTATION_PERFORMED_FIX_178,
)
from aethos_core.mission_control.frozen_gate_intake_preview.frozen_gate_intake_preview_intent import (
    is_frozen_gate_intake_preview_intent,
    parse_frozen_gate_intake_preview_record_intent,
)
from aethos_core.mission_control.frozen_gate_intake_preview.frozen_gate_intake_preview_renderer import (
    render_frozen_gate_intake_preview,
)
from aethos_core.mission_control.frozen_gate_intake_preview.frozen_gate_intake_preview_service import (
    build_frozen_gate_intake_preview,
)
from aethos_core.mission_control.frozen_gate_intake_preview.frozen_gate_intake_preview_store import (
    append_frozen_gate_intake_preview_record,
)
from aethos_core.mission_control.gate_routed_lane_entry_handoff.gate_routed_lane_entry_handoff_service import (
    build_gate_routed_lane_entry_handoff,
)


def _meta(session_id: str, *, stage: str, **extra: str) -> dict[str, str]:
    return {
        "route_id": FROZEN_GATE_INTAKE_PREVIEW_ROUTE_ID,
        "matched_module": "mission_control.frozen_gate_intake_preview.frozen_gate_intake_preview_router",
        "session_id": session_id,
        "readonly": "true",
        "mutation_performed": "false" if MUTATION_PERFORMED_FIX_178 is False else "true",
        "execution_performed": "false" if EXECUTION_PERFORMED_FIX_178 is False else "true",
        "gate_execution_performed": "false" if GATE_EXECUTION_PERFORMED_FIX_178 is False else "true",
        "lane_entry_execution_performed": "false" if LANE_ENTRY_EXECUTION_PERFORMED_FIX_178 is False else "true",
        "lane_admission_executed": "false" if LANE_ADMISSION_EXECUTED_FIX_178 is False else "true",
        "autonomous_execution_enabled": "false" if AUTONOMOUS_EXECUTION_ENABLED_FIX_178 is False else "true",
        "autonomous_lane_entry_enabled": "false" if AUTONOMOUS_LANE_ENTRY_ENABLED_FIX_178 is False else "true",
        "gate_bypass_enabled": "false" if GATE_BYPASS_ENABLED_FIX_178 is False else "true",
        "mutation_scope": "frozen_gate_intake_preview_memory_only",
        "presentation_bypass": "true",
        "presentation_mode": "engineering",
        "suppress_governance_footer": "true",
        "mission_control_stage": stage,
        "lane_separation": "gate_intake_preview_not_gate_execution",
        **extra,
    }


def route_frozen_gate_intake_preview(
    text: str,
    *,
    session_id: str = "default",
) -> tuple[str, str, dict[str, str]] | None:
    record_intent = parse_frozen_gate_intake_preview_record_intent(text)
    if record_intent is not None:
        kind, content = record_intent
        handoff = build_gate_routed_lane_entry_handoff(session_id=session_id)
        ctx = handoff.gate_routed_lane_entry_handoff if handoff.ok else {}
        record, blockers = append_frozen_gate_intake_preview_record(
            session_id=session_id,
            kind=kind,
            content=content,
            plan_id=str(ctx.get("plan_id") or "") or None,
            correlation_id=str(ctx.get("correlation_id") or "") or None,
        )
        if blockers or not record:
            body = f"Frozen gate intake preview record blocked: {', '.join(blockers)}"
            return (
                body,
                "mission_control_frozen_gate_intake_preview_record_blocked",
                _meta(session_id, stage="blocked"),
            )
        body = (
            f"Gate intake preview record persisted (`{record.get('record_id')}`, kind `{kind}`). "
            "Preview only — frozen gate executes only in governed lane."
        )
        return (
            body,
            "mission_control_frozen_gate_intake_preview_record",
            _meta(
                session_id,
                stage="frozen_gate_intake_preview_record",
                record_id=str(record.get("record_id") or ""),
                frozen_gate_intake_preview_memory_only="true",
            ),
        )

    if not is_frozen_gate_intake_preview_intent(text):
        return None

    result = build_frozen_gate_intake_preview(session_id=session_id)
    if not result.ok:
        body = f"Frozen gate intake preview unavailable: {', '.join(result.blockers)}"
        return (
            body,
            "mission_control_frozen_gate_intake_preview_blocked",
            _meta(session_id, stage="blocked"),
        )

    body = render_frozen_gate_intake_preview(result.frozen_gate_intake_preview)
    return (
        body,
        "mission_control_frozen_gate_intake_preview",
        _meta(
            session_id,
            stage="frozen_gate_intake_preview",
            intake_preview_record_count=str(
                result.frozen_gate_intake_preview.get("intake_preview_record_count", 0)
            ),
        ),
    )

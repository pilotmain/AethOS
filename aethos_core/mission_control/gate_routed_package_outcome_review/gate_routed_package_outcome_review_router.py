# SPDX-License-Identifier: Apache-2.0
"""FIX 173 — chat router for gate-routed package outcome review."""

from __future__ import annotations

from aethos_core.mission_control.gate_routed_package_outcome_review.gate_routed_package_outcome_review_contract import (
    AUTONOMOUS_EXECUTION_ENABLED_FIX_173,
    AUTONOMOUS_LANE_ENTRY_ENABLED_FIX_173,
    EXECUTION_PERFORMED_FIX_173,
    GATE_BYPASS_ENABLED_FIX_173,
    GATE_ROUTED_PACKAGE_OUTCOME_REVIEW_ROUTE_ID,
    MUTATION_PERFORMED_FIX_173,
)
from aethos_core.mission_control.gate_routed_package_outcome_review.gate_routed_package_outcome_review_intent import (
    is_gate_routed_package_outcome_review_intent,
    parse_gate_routed_package_outcome_review_record_intent,
)
from aethos_core.mission_control.gate_routed_package_outcome_review.gate_routed_package_outcome_review_renderer import (
    render_gate_routed_package_outcome_review,
)
from aethos_core.mission_control.gate_routed_package_outcome_review.gate_routed_package_outcome_review_service import (
    build_gate_routed_package_outcome_review,
)
from aethos_core.mission_control.gate_routed_package_outcome_review.gate_routed_package_outcome_review_store import (
    append_gate_routed_package_outcome_review_record,
)
from aethos_core.mission_control.governed_task_execution_coordination.governed_task_execution_coordination_service import (
    build_governed_task_execution_coordination,
)


def _meta(session_id: str, *, stage: str, **extra: str) -> dict[str, str]:
    return {
        "route_id": GATE_ROUTED_PACKAGE_OUTCOME_REVIEW_ROUTE_ID,
        "matched_module": "mission_control.gate_routed_package_outcome_review.gate_routed_package_outcome_review_router",
        "session_id": session_id,
        "readonly": "true",
        "mutation_performed": "false" if MUTATION_PERFORMED_FIX_173 is False else "true",
        "execution_performed": "false" if EXECUTION_PERFORMED_FIX_173 is False else "true",
        "autonomous_execution_enabled": "false" if AUTONOMOUS_EXECUTION_ENABLED_FIX_173 is False else "true",
        "autonomous_lane_entry_enabled": "false" if AUTONOMOUS_LANE_ENTRY_ENABLED_FIX_173 is False else "true",
        "gate_bypass_enabled": "false" if GATE_BYPASS_ENABLED_FIX_173 is False else "true",
        "mutation_scope": "gate_routed_package_outcome_review_memory_only",
        "presentation_bypass": "true",
        "presentation_mode": "engineering",
        "suppress_governance_footer": "true",
        "mission_control_stage": stage,
        "lane_separation": "outcome_review_not_lane_execution",
        **extra,
    }


def route_gate_routed_package_outcome_review(
    text: str,
    *,
    session_id: str = "default",
) -> tuple[str, str, dict[str, str]] | None:
    record_intent = parse_gate_routed_package_outcome_review_record_intent(text)
    if record_intent is not None:
        kind, content = record_intent
        coordination = build_governed_task_execution_coordination(session_id=session_id)
        board = coordination.governed_task_execution_coordination if coordination.ok else {}
        record, blockers = append_gate_routed_package_outcome_review_record(
            session_id=session_id,
            kind=kind,
            content=content,
            plan_id=str(board.get("plan_id") or "") or None,
            correlation_id=str(board.get("correlation_id") or "") or None,
        )
        if blockers or not record:
            body = f"Gate-routed package outcome review record blocked: {', '.join(blockers)}"
            return (
                body,
                "mission_control_gate_routed_package_outcome_review_record_blocked",
                _meta(session_id, stage="blocked"),
            )
        body = (
            f"Gate review record persisted (`{record.get('record_id')}`, kind `{kind}`). "
            "Review only — existing frozen gates decide lane action."
        )
        return (
            body,
            "mission_control_gate_routed_package_outcome_review_record",
            _meta(
                session_id,
                stage="gate_routed_package_outcome_review_record",
                record_id=str(record.get("record_id") or ""),
                gate_routed_package_outcome_review_memory_only="true",
            ),
        )

    if not is_gate_routed_package_outcome_review_intent(text):
        return None

    result = build_gate_routed_package_outcome_review(session_id=session_id)
    if not result.ok:
        body = f"Gate-routed package outcome review unavailable: {', '.join(result.blockers)}"
        return (
            body,
            "mission_control_gate_routed_package_outcome_review_blocked",
            _meta(session_id, stage="blocked"),
        )

    body = render_gate_routed_package_outcome_review(result.gate_routed_package_outcome_review)
    return (
        body,
        "mission_control_gate_routed_package_outcome_review",
        _meta(
            session_id,
            stage="gate_routed_package_outcome_review",
            gate_review_record_count=str(
                result.gate_routed_package_outcome_review.get("gate_review_record_count", 0)
            ),
        ),
    )

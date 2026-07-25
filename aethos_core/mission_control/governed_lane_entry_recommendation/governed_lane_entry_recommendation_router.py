# SPDX-License-Identifier: Apache-2.0
"""FIX 174 — chat router for governed lane entry recommendation."""

from __future__ import annotations

from aethos_core.mission_control.gate_routed_package_outcome_review.gate_routed_package_outcome_review_service import (
    build_gate_routed_package_outcome_review,
)
from aethos_core.mission_control.governed_lane_entry_recommendation.governed_lane_entry_recommendation_contract import (
    AUTONOMOUS_EXECUTION_ENABLED_FIX_174,
    AUTONOMOUS_LANE_ENTRY_ENABLED_FIX_174,
    EXECUTION_PERFORMED_FIX_174,
    GATE_BYPASS_ENABLED_FIX_174,
    GOVERNED_LANE_ENTRY_RECOMMENDATION_ROUTE_ID,
    LANE_ADMISSION_PERFORMED_FIX_174,
    MUTATION_PERFORMED_FIX_174,
)
from aethos_core.mission_control.governed_lane_entry_recommendation.governed_lane_entry_recommendation_intent import (
    is_governed_lane_entry_recommendation_intent,
    parse_governed_lane_entry_recommendation_record_intent,
)
from aethos_core.mission_control.governed_lane_entry_recommendation.governed_lane_entry_recommendation_renderer import (
    render_governed_lane_entry_recommendation,
)
from aethos_core.mission_control.governed_lane_entry_recommendation.governed_lane_entry_recommendation_service import (
    build_governed_lane_entry_recommendation,
)
from aethos_core.mission_control.governed_lane_entry_recommendation.governed_lane_entry_recommendation_store import (
    append_governed_lane_entry_recommendation_record,
)


def _meta(session_id: str, *, stage: str, **extra: str) -> dict[str, str]:
    return {
        "route_id": GOVERNED_LANE_ENTRY_RECOMMENDATION_ROUTE_ID,
        "matched_module": "mission_control.governed_lane_entry_recommendation.governed_lane_entry_recommendation_router",
        "session_id": session_id,
        "readonly": "true",
        "mutation_performed": "false" if MUTATION_PERFORMED_FIX_174 is False else "true",
        "execution_performed": "false" if EXECUTION_PERFORMED_FIX_174 is False else "true",
        "lane_admission_performed": "false" if LANE_ADMISSION_PERFORMED_FIX_174 is False else "true",
        "autonomous_execution_enabled": "false" if AUTONOMOUS_EXECUTION_ENABLED_FIX_174 is False else "true",
        "autonomous_lane_entry_enabled": "false" if AUTONOMOUS_LANE_ENTRY_ENABLED_FIX_174 is False else "true",
        "gate_bypass_enabled": "false" if GATE_BYPASS_ENABLED_FIX_174 is False else "true",
        "mutation_scope": "governed_lane_entry_recommendation_memory_only",
        "presentation_bypass": "true",
        "presentation_mode": "engineering",
        "suppress_governance_footer": "true",
        "mission_control_stage": stage,
        "lane_separation": "lane_recommendation_not_lane_admission",
        **extra,
    }


def route_governed_lane_entry_recommendation(
    text: str,
    *,
    session_id: str = "default",
) -> tuple[str, str, dict[str, str]] | None:
    record_intent = parse_governed_lane_entry_recommendation_record_intent(text)
    if record_intent is not None:
        kind, content = record_intent
        review = build_gate_routed_package_outcome_review(session_id=session_id)
        board = review.gate_routed_package_outcome_review if review.ok else {}
        record, blockers = append_governed_lane_entry_recommendation_record(
            session_id=session_id,
            kind=kind,
            content=content,
            plan_id=str(board.get("plan_id") or "") or None,
            correlation_id=str(board.get("correlation_id") or "") or None,
        )
        if blockers or not record:
            body = f"Governed lane entry recommendation record blocked: {', '.join(blockers)}"
            return (
                body,
                "mission_control_governed_lane_entry_recommendation_record_blocked",
                _meta(session_id, stage="blocked"),
            )
        body = (
            f"Lane recommendation record persisted (`{record.get('record_id')}`, kind `{kind}`). "
            "Recommendation only — frozen gates and human decide admission."
        )
        return (
            body,
            "mission_control_governed_lane_entry_recommendation_record",
            _meta(
                session_id,
                stage="governed_lane_entry_recommendation_record",
                record_id=str(record.get("record_id") or ""),
                governed_lane_entry_recommendation_memory_only="true",
            ),
        )

    if not is_governed_lane_entry_recommendation_intent(text):
        return None

    result = build_governed_lane_entry_recommendation(session_id=session_id)
    if not result.ok:
        body = f"Governed lane entry recommendation unavailable: {', '.join(result.blockers)}"
        return (
            body,
            "mission_control_governed_lane_entry_recommendation_blocked",
            _meta(session_id, stage="blocked"),
        )

    body = render_governed_lane_entry_recommendation(result.governed_lane_entry_recommendation)
    return (
        body,
        "mission_control_governed_lane_entry_recommendation",
        _meta(
            session_id,
            stage="governed_lane_entry_recommendation",
            lane_recommendation_record_count=str(
                result.governed_lane_entry_recommendation.get("lane_recommendation_record_count", 0)
            ),
        ),
    )

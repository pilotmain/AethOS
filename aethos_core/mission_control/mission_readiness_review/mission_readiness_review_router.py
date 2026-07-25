# SPDX-License-Identifier: Apache-2.0
"""FIX 147 — chat router for mission readiness review board."""

from __future__ import annotations

from aethos_core.mission_control.mission_readiness_review.mission_readiness_review_contract import (
    EXECUTION_AUTHORITY_DELEGATED_FIX_147,
    HUMAN_REVIEW_REQUIRED_FIX_147,
    MISSION_READINESS_REVIEW_ROUTE_ID,
    MUTATION_PERFORMED_FIX_147,
)
from aethos_core.mission_control.mission_readiness_review.mission_readiness_review_intent import (
    is_mission_readiness_review_intent,
)
from aethos_core.mission_control.mission_readiness_review.mission_readiness_review_renderer import (
    render_mission_readiness_review,
)
from aethos_core.mission_control.mission_readiness_review.mission_readiness_review_service import (
    build_mission_readiness_review,
)


def _meta(session_id: str, *, stage: str, **extra: str) -> dict[str, str]:
    return {
        "route_id": MISSION_READINESS_REVIEW_ROUTE_ID,
        "matched_module": "mission_control.mission_readiness_review.mission_readiness_review_router",
        "session_id": session_id,
        "readonly": "true",
        "mutation_performed": "false" if MUTATION_PERFORMED_FIX_147 is False else "true",
        "human_review_required": "true" if HUMAN_REVIEW_REQUIRED_FIX_147 is True else "false",
        "execution_authority_delegated": "false"
        if EXECUTION_AUTHORITY_DELEGATED_FIX_147 is False
        else "true",
        "mutation_scope": "mission_readiness_review_only",
        "presentation_bypass": "true",
        "presentation_mode": "engineering",
        "suppress_governance_footer": "true",
        "mission_control_stage": stage,
        "lane_separation": "readiness_review_not_execution",
        **extra,
    }


def route_mission_readiness_review(
    text: str,
    *,
    session_id: str = "default",
) -> tuple[str, str, dict[str, str]] | None:
    if not is_mission_readiness_review_intent(text):
        return None

    result = build_mission_readiness_review(session_id=session_id)
    if not result.ok:
        body = f"Mission readiness review unavailable: {', '.join(result.blockers)}"
        return body, "mission_control_mission_readiness_review_blocked", _meta(session_id, stage="blocked")

    body = render_mission_readiness_review(result.review)
    go_rec = (result.review.get("sections") or {}).get("go_no_go_hold_recommendation") or {}
    return (
        body,
        "mission_control_mission_readiness_review",
        _meta(
            session_id,
            stage="mission_readiness_review",
            go_no_go_hold=str(go_rec.get("recommendation", "")),
            recommendation_count=str(result.review.get("recommendation_count", 0)),
        ),
    )

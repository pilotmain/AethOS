# SPDX-License-Identifier: Apache-2.0
"""FIX 141 — chat router for mission knowledge spaces."""

from __future__ import annotations

from aethos_core.mission_control.knowledge_spaces.knowledge_spaces_contract import (
    AUTOMATIC_MUTATION_PLANNING_ENABLED_FIX_141,
    AUTONOMOUS_ACTION_ENABLED_FIX_141,
    KNOWLEDGE_SPACES_ROUTE_ID,
    MUTATION_PERFORMED_FIX_141,
)
from aethos_core.mission_control.knowledge_spaces.knowledge_spaces_intent import (
    extract_knowledge_query,
    is_knowledge_spaces_intent,
)
from aethos_core.mission_control.knowledge_spaces.knowledge_spaces_renderer import render_knowledge_spaces_search
from aethos_core.mission_control.knowledge_spaces.knowledge_spaces_service import search_mission_knowledge_spaces


def _meta(session_id: str, *, stage: str, **extra: str) -> dict[str, str]:
    return {
        "route_id": KNOWLEDGE_SPACES_ROUTE_ID,
        "matched_module": "mission_control.knowledge_spaces.knowledge_spaces_router",
        "session_id": session_id,
        "readonly": "true",
        "mutation_performed": "false" if MUTATION_PERFORMED_FIX_141 is False else "true",
        "autonomous_action_enabled": "false" if AUTONOMOUS_ACTION_ENABLED_FIX_141 is False else "true",
        "automatic_mutation_planning_enabled": "false"
        if AUTOMATIC_MUTATION_PLANNING_ENABLED_FIX_141 is False
        else "true",
        "mutation_scope": "knowledge_retrieval_only",
        "presentation_bypass": "true",
        "presentation_mode": "engineering",
        "suppress_governance_footer": "true",
        "mission_control_stage": stage,
        "lane_separation": "intelligence_not_execution",
        **extra,
    }


def route_knowledge_spaces(
    text: str,
    *,
    session_id: str = "default",
) -> tuple[str, str, dict[str, str]] | None:
    if not is_knowledge_spaces_intent(text):
        return None

    query = extract_knowledge_query(text)
    result = search_mission_knowledge_spaces(session_id=session_id, query=query, text=text, ingest_current=True)
    if not result.ok:
        body = f"Knowledge space search unavailable: {', '.join(result.blockers)}"
        return body, "mission_control_knowledge_spaces_blocked", _meta(session_id, stage="blocked")

    body = render_knowledge_spaces_search(result.payload)
    seen = result.payload.get("seen_before") or {}
    return (
        body,
        "mission_control_knowledge_spaces",
        _meta(
            session_id,
            stage="knowledge_spaces",
            query=str(result.payload.get("query") or ""),
            seen_before=str(seen.get("likely_seen_before", False)),
            hit_count=str(len(result.payload.get("search_results") or [])),
        ),
    )

# SPDX-License-Identifier: Apache-2.0
"""FIX 140 — chat router for cross-session organizational memory."""

from __future__ import annotations

from aethos_core.mission_control.operational_memory.cross_session.cross_session_contract import (
    AUTONOMOUS_ADAPTATION_ENABLED_FIX_140,
    CROSS_SESSION_MEMORY_ROUTE_ID,
    MUTATION_PERFORMED_FIX_140,
)
from aethos_core.mission_control.operational_memory.cross_session.cross_session_intent import (
    is_cross_session_memory_intent,
)
from aethos_core.mission_control.operational_memory.cross_session.cross_session_renderer import (
    render_cross_session_operational_memory,
)
from aethos_core.mission_control.operational_memory.cross_session.cross_session_service import (
    build_cross_session_operational_memory,
)


def _meta(session_id: str, *, stage: str, **extra: str) -> dict[str, str]:
    return {
        "route_id": CROSS_SESSION_MEMORY_ROUTE_ID,
        "matched_module": "mission_control.operational_memory.cross_session.cross_session_router",
        "session_id": session_id,
        "readonly": "true",
        "mutation_performed": "false" if MUTATION_PERFORMED_FIX_140 is False else "true",
        "autonomous_adaptation_enabled": "false"
        if AUTONOMOUS_ADAPTATION_ENABLED_FIX_140 is False
        else "true",
        "mutation_scope": "cross_session_memory_only",
        "presentation_bypass": "true",
        "presentation_mode": "engineering",
        "suppress_governance_footer": "true",
        "mission_control_stage": stage,
        "lane_separation": "organizational_memory_not_mutation",
        **extra,
    }


def route_cross_session_operational_memory(
    text: str,
    *,
    session_id: str = "default",
) -> tuple[str, str, dict[str, str]] | None:
    if not is_cross_session_memory_intent(text):
        return None

    result = build_cross_session_operational_memory(session_id=session_id, ingest_current=True)
    if not result.ok:
        body = f"Cross-session operational memory unavailable: {', '.join(result.blockers)}"
        return body, "mission_control_cross_session_memory_blocked", _meta(session_id, stage="blocked")

    body = render_cross_session_operational_memory(result.memory)
    return (
        body,
        "mission_control_cross_session_memory",
        _meta(
            session_id,
            stage="cross_session_memory",
            persisted_records=str(result.memory.get("persisted_record_count", 0)),
        ),
    )

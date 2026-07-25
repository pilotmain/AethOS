# SPDX-License-Identifier: Apache-2.0
"""FIX 139 — chat router for operational memory graph."""

from __future__ import annotations

from aethos_core.mission_control.operational_memory.operational_memory_contract import (
    AUTONOMOUS_ADAPTATION_ENABLED_FIX_139,
    MUTATION_PERFORMED_FIX_139,
    OPERATIONAL_MEMORY_ROUTE_ID,
)
from aethos_core.mission_control.operational_memory.operational_memory_intent import is_operational_memory_intent
from aethos_core.mission_control.operational_memory.operational_memory_renderer import render_operational_memory_graph
from aethos_core.mission_control.operational_memory.operational_memory_service import build_operational_memory_graph


def _meta(session_id: str, *, stage: str, **extra: str) -> dict[str, str]:
    return {
        "route_id": OPERATIONAL_MEMORY_ROUTE_ID,
        "matched_module": "mission_control.operational_memory.operational_memory_router",
        "session_id": session_id,
        "readonly": "true",
        "mutation_performed": "false" if MUTATION_PERFORMED_FIX_139 is False else "true",
        "autonomous_adaptation_enabled": "false"
        if AUTONOMOUS_ADAPTATION_ENABLED_FIX_139 is False
        else "true",
        "mutation_scope": "operational_memory_only",
        "presentation_bypass": "true",
        "presentation_mode": "engineering",
        "suppress_governance_footer": "true",
        "mission_control_stage": stage,
        "lane_separation": "memory_not_mutation",
        **extra,
    }


def route_operational_memory(
    text: str,
    *,
    session_id: str = "default",
) -> tuple[str, str, dict[str, str]] | None:
    if not is_operational_memory_intent(text):
        return None

    result = build_operational_memory_graph(session_id=session_id)
    if not result.ok:
        body = f"Operational memory unavailable: {', '.join(result.blockers)}"
        return body, "mission_control_operational_memory_blocked", _meta(session_id, stage="blocked")

    graph = result.graph
    body = render_operational_memory_graph(graph)
    stats = (graph.get("graph") or {}).get("stats") or {}
    return (
        body,
        "mission_control_operational_memory",
        _meta(
            session_id,
            stage="operational_memory",
            plan_id=str(graph.get("plan_id") or ""),
            correlation_id=str(graph.get("correlation_id") or ""),
            node_count=str(stats.get("node_count", 0)),
        ),
    )

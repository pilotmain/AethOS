# SPDX-License-Identifier: Apache-2.0
"""Investigation output runtime — intermediate conclusions from active agents."""

from __future__ import annotations

from typing import Any

from aethos_core.execution_progress_tracking.progress_tracker import advance_execution_progress, get_execution_progress
from aethos_core.investigative_narrative.narrative_composer import enrich_investigative_narrative
from aethos_core.operational_deliverables.deliverable_templates import get_agent_deliverable
from aethos_core.operational_entity_runtime.lightweight_agent_registry import list_active_entities


def compose_investigation_output(
    *,
    session_id: str = "default",
    agent_name: str | None = None,
    advance: bool = True,
) -> dict[str, Any]:
    entities = list_active_entities(session_id=session_id)
    if not entities:
        return {"available": False, "reply": None}

    target = agent_name
    if not target:
        target = str(entities[0].get("name") or "Operational agent")

    if advance:
        state = advance_execution_progress(session_id=session_id, agent_name=target)
    else:
        state = get_execution_progress(session_id=session_id)

    stage = max(int(state.get("stage") or 1), 1)
    deliverable = get_agent_deliverable(agent_name=target, stage=stage)
    findings = "\n".join(f"{i + 1}. {f}" for i, f in enumerate(deliverable.get("findings") or []))
    base_reply = (
        f"{deliverable['headline']}\n\n"
        f"{findings}\n\n"
        f"{deliverable.get('conclusion') or ''}"
    ).strip()

    other_agents = [
        e.get("name")
        for e in entities
        if str(e.get("name") or "").lower() != target.lower()
    ]
    if other_agents and stage >= 2:
        other = other_agents[0]
        other_deliverable = get_agent_deliverable(agent_name=str(other), stage=stage)
        base_reply += f"\n\n{other_deliverable['headline']}\n"
        other_findings = other_deliverable.get("findings") or []
        if other_findings:
            base_reply += "\n".join(f"- {f}" for f in other_findings[:3])

    reply = enrich_investigative_narrative(
        session_id=session_id,
        agent_name=deliverable["agent_name"],
        stage=stage,
        base_reply=base_reply,
        deliverable=deliverable,
        record=advance,
    )

    return {
        "available": True,
        "reply": reply,
        "agent_name": deliverable["agent_name"],
        "stage": stage,
        "deliverable": deliverable,
        "investigative_continuity": True,
    }

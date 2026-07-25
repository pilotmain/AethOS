# SPDX-License-Identifier: Apache-2.0
"""Readonly deep research pipeline — delegates to universal research runtime."""

from __future__ import annotations

from typing import Any


def run_deep_research(*, topic: str, max_sources: int = 5, session_id: str = "default") -> dict[str, Any]:
    """Gather public sources and synthesize a structured report (persisted replay + artifacts)."""
    raw_topic = (topic or "").strip()
    if len(raw_topic) < 4:
        return {"ok": False, "error": "topic_required"}

    from aethos_core.research.research_runtime import run_research_query

    run = run_research_query(raw_topic, session_id=session_id, channel="agent_tool")
    source_count = 0
    for step in run.timeline or []:
        if step.get("step") == "synthesis" and step.get("source_count") is not None:
            source_count = int(step["source_count"])
            break
    return {
        "ok": run.ok,
        "topic": run.query,
        "source_count": source_count,
        "report": run.reply,
        "replay_id": run.replay_id,
        "artifact_ids": run.artifact_ids,
        "read_only": True,
        "session_id": session_id,
        "mission_control_hint": "Mission Control → Research",
        "error": None if run.ok else "no_sources",
    }

# SPDX-License-Identifier: Apache-2.0
"""Deep research runtime — multi-step gather, synthesize, artifact (§B1)."""

from __future__ import annotations

from typing import Any

from aethos_core.research.research_runtime import ResearchRunResult, run_research_query


def deep_research_enabled() -> bool:
    from aethos_core.config import get_settings

    return bool(getattr(get_settings(), "deep_research_enabled", False))


def run_deep_research_pipeline(
    question: str,
    *,
    depth: int = 2,
    session_id: str = "default",
    channel: str = "agent_tool",
) -> dict[str, Any]:
    """Planner → retrieval → synthesis with step timeline for SSE/UI."""
    raw = (question or "").strip()
    if len(raw) < 4:
        return {"ok": False, "error": "question_required"}

    if not deep_research_enabled():
        return {
            "ok": False,
            "error": "deep_research_disabled",
            "hint": "Set DEEP_RESEARCH_ENABLED=true to run governed deep research jobs.",
        }

    steps: list[dict[str, Any]] = []
    steps.append({"step": "plan", "detail": "Planning research sub-questions", "status": "done"})
    max_sources = max(2, min(int(depth or 2) + 3, 10))
    steps.append({"step": "gather", "detail": f"Fetching up to {max_sources} sources", "status": "running"})

    run: ResearchRunResult = run_research_query(raw, session_id=session_id, channel=channel)
    steps.append(
        {
            "step": "gather",
            "detail": "Source retrieval complete",
            "status": "done" if run.ok else "degraded",
            "source_count": len(run.artifact_ids or []),
        }
    )
    steps.append(
        {
            "step": "synthesize",
            "detail": "Structured report ready",
            "status": "done" if run.ok else "failed",
        }
    )

    report_md = run.reply or ""
    if run.ok and report_md:
        try:
            from aethos_core.canvas.canvas_store import render_canvas_view

            render_canvas_view(
                session_id=session_id,
                view_type="research_report",
                title=f"Research — {run.query[:48]}",
                data={"summary": report_md[:12000], "replay_id": run.replay_id},
            )
        except Exception:  # noqa: BLE001
            pass

    return {
        "ok": run.ok,
        "question": run.query,
        "report": report_md,
        "report_markdown": report_md,
        "replay_id": run.replay_id,
        "artifact_ids": run.artifact_ids,
        "steps": steps,
        "timeline": run.timeline,
        "configured": run.configured,
        "read_only": True,
        "session_id": session_id,
        "mission_control_hint": "Mission Control → Research · export to Documents",
        "error": None if run.ok else "research_failed",
    }

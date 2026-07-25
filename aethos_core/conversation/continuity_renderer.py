# SPDX-License-Identifier: Apache-2.0
"""Continuity renderer — natural, grounded resume text from memory."""

from __future__ import annotations

from typing import Any


def _memory_is_thin(record: dict[str, Any], *, has_threads: bool) -> bool:
    if has_threads:
        return False
    return not (record.get("phase") and (record.get("resolved") or record.get("focus")))


def render_continuity_resume(
    *,
    session_id: str = "default",
    lookback_hours: float = 48,
) -> dict[str, Any]:
    """Turn continuity memory into operator-useful natural resume text."""
    from aethos_core.conversation.conversation_runtime import get_conversational_goal
    from aethos_core.conversation.operational_memory import build_continuity_context
    from aethos_core.human_centered.continuity_memory import load_continuity_memory, seed_default_continuity
    from aethos_core.relational.conversational_memory import recent_context
    from aethos_core.trust.explainability_envelope import wrap_with_explainability

    import json
    from pathlib import Path

    seed_default_continuity(session_id=session_id)
    record = load_continuity_memory(session_id=session_id)
    operational = build_continuity_context(session_id=session_id)
    goal = get_conversational_goal(session_id=session_id)
    recent_turns = recent_context(session_id=session_id, limit=6)

    conv_root = Path(__file__).resolve().parents[2] / "data" / "conversation" / f"session_{session_id}.json"
    threads: list[dict[str, Any]] = []
    if conv_root.is_file():
        try:
            threads = json.loads(conv_root.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            pass

    thin = _memory_is_thin(record, has_threads=bool(threads))
    confidence = float(record.get("confidence") or 0.65)
    if thin:
        confidence = min(confidence, 0.55)

    thread_topics: list[str] = []
    thread_unresolved: list[str] = []
    for t in threads[:3]:
        thread_topics.extend(t.get("topics") or [])
        thread_unresolved.extend(t.get("unresolved") or [])

    phase = record.get("phase") or "recent work"
    focus = record.get("focus") or record.get("current_system_focus") or operational.get("last_focus")
    if thread_topics and not record.get("phase"):
        focus = thread_topics[0]
    lines: list[str] = []

    if lookback_hours >= 20:
        lines.append(f"We were working on **Phase {phase}** — {focus}.")
    else:
        lines.append(f"We were stabilizing **{focus}** after recent Living Intelligence work.")

    resolved = list(record.get("resolved") or [])
    if thread_topics and threads:
        lines.append("")
        lines.append("**We were investigating:**")
        for t in list(dict.fromkeys(thread_topics))[:4]:
            lines.append(f"- {t}")

    if resolved:
        lines.append("")
        lines.append("**Resolved:**")
        for item in resolved[:4]:
            lines.append(f"- {item}")

    latest_resolved = resolved[0] if resolved else None
    if latest_resolved and "404" in latest_resolved:
        lines.append("")
        lines.append(
            "The latest resolved issue was `/human/living` returning 404 because "
            "`humanApi.ts` used relative fetch instead of `mcFetch` to the FastAPI backend."
        )

    unresolved = list(dict.fromkeys((record.get("unresolved") or []) + thread_unresolved + (operational.get("unresolved_issues") or [])))[:5]
    if unresolved:
        lines.append("")
        lines.append("**Still open:**")
        for u in unresolved[:3]:
            lines.append(f"- {u}")

    pending = record.get("pending_validation") or []
    if pending:
        lines.append("")
        lines.append("**Pending your validation:**")
        for p in pending[:3]:
            lines.append(f"- {p}")

    investigations = operational.get("active_investigations") or []
    collab = record.get("collaboration_context") or []
    if collab or investigations:
        lines.append("")
        lines.append("**Collaboration context:**")
        for c in (collab + investigations)[:3]:
            lines.append(f"- {c}")

    next_step = record.get("next_best_step")
    if next_step:
        lines.append("")
        lines.append(f"**Next best step:** {next_step}")

    if goal.get("goal"):
        lines.append("")
        lines.append(f"**Active goal:** {goal['goal']}")

    lines.append("")
    lines.append(f"*{record.get('governance', 'No autonomous action')} taken.*")

    if thin:
        lines.append("")
        lines.append(
            "*Note: continuity memory is thin — I'll be more specific as we work together "
            "and you validate steps in Mission Control.*"
        )

    resume_core = "\n".join(lines)
    missing: list[str] = []
    if not record.get("evidence_refs"):
        missing.append("limited evidence refs")
    if thin:
        missing.append("sparse session history")

    explained = wrap_with_explainability(
        conclusion=resume_core,
        confidence=confidence,
        reasons=["continuity memory", "operational context", "conversation threads"] if not thin else ["continuity memory (thin)"],
        evidence_sources=record.get("evidence_refs") or ["continuity_memory"],
        missing_evidence=missing or None,
        replay_trace=(record.get("replay_refs") or ["continuity_chain"])[0],
    )

    return {
        "ok": True,
        "resume_text": explained.get("full_text", resume_core),
        "resume_core": resume_core,
        "phase": phase,
        "focus": focus,
        "resolved": resolved,
        "unresolved": unresolved,
        "pending_validation": pending,
        "next_best_step": next_step,
        "confidence": confidence,
        "thin_memory": thin,
        "recent_turns": recent_turns,
        "goal": goal,
        "explainability": explained.get("explainability"),
        "governance": record.get("governance"),
        "autonomous_execution_blocked": True,
    }

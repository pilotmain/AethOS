# SPDX-License-Identifier: Apache-2.0
"""Conversation runtime — fluid, contextual, deeply human dialogue."""

from __future__ import annotations

import json
from time import time
from typing import Any

from pathlib import Path

_NS_THREADS = "conversation_threads"
_NS_GOALS = "conversation_goals"


def _conv_root() -> Path:
    root = Path(__file__).resolve().parents[2] / "data" / "conversation"
    root.mkdir(parents=True, exist_ok=True)
    return root


def _session_key(session_id: str) -> str:
    return (session_id or "default").strip() or "default"


def _load_threads(session_id: str) -> list[dict[str, Any]]:
    from aethos_core.tenancy.tenant_data_store import get_record

    stored = get_record(_NS_THREADS, _session_key(session_id), default=None)
    if isinstance(stored, list):
        return stored
    # Legacy file import (single-tenant migration, default tenant only).
    path = _conv_root() / f"session_{_session_key(session_id)}.json"
    if path.is_file():
        try:
            threads = json.loads(path.read_text(encoding="utf-8"))
            if isinstance(threads, list):
                from aethos_core.tenancy.tenant_data_store import set_record

                set_record(_NS_THREADS, _session_key(session_id), threads)
                return threads
        except (OSError, json.JSONDecodeError):
            pass
    return []


def _save_threads(session_id: str, threads: list[dict[str, Any]]) -> None:
    from aethos_core.tenancy.tenant_data_store import set_record

    set_record(_NS_THREADS, _session_key(session_id), threads[:30])


def record_conversation_thread(
    *,
    session_id: str = "default",
    topics: list[str],
    unresolved: list[str] | None = None,
    summary: str = "",
) -> None:
    from aethos_core.conversation.operational_memory import record_focus_recovery, track_unresolved_issue

    threads = _load_threads(session_id)
    threads.insert(
        0,
        {
            "at": time(),
            "topics": topics[:8],
            "unresolved": (unresolved or [])[:8],
            "summary": summary[:400],
            "day": time(),
        },
    )
    _save_threads(session_id, threads)

    for topic in topics[:4]:
        record_focus_recovery(session_id=session_id, focus=topic, channel="chat")
    for issue in (unresolved or [])[:4]:
        track_unresolved_issue(session_id=session_id, issue=issue)


def set_conversational_goal(*, session_id: str = "default", goal: str, steps: list[str] | None = None) -> None:
    from aethos_core.tenancy.tenant_data_store import set_record

    record = {"goal": goal, "steps": steps or [], "started_at": time(), "status": "active"}
    set_record(_NS_GOALS, _session_key(session_id), record)


def get_conversational_goal(*, session_id: str = "default") -> dict[str, Any]:
    from aethos_core.tenancy.tenant_data_store import get_record, set_record

    stored = get_record(_NS_GOALS, _session_key(session_id), default={})
    if isinstance(stored, dict) and stored:
        return stored
    path = _conv_root() / f"goals_{_session_key(session_id)}.json"
    if path.is_file():
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
            if isinstance(data, dict):
                set_record(_NS_GOALS, _session_key(session_id), data)
                return data
        except (OSError, json.JSONDecodeError):
            pass
    return {}


def resume_conversation(*, session_id: str = "default", lookback_hours: float = 48) -> dict[str, Any]:
    """Continue where we left off — grounded continuity renderer."""
    from aethos_core.conversation.continuity_renderer import render_continuity_resume

    rendered = render_continuity_resume(session_id=session_id, lookback_hours=lookback_hours)
    return rendered


def get_conversation_status(*, session_id: str = "default") -> dict[str, Any]:
    resume = resume_conversation(session_id=session_id)
    return {
        "ok": True,
        "phase": "10.1.2",
        "features": {
            "conversational_continuity": True,
            "interruption_recovery": True,
            "layered_memory_recall": True,
            "contextual_follow_through": True,
            "adaptive_explanation_depth": True,
            "intent_persistence": bool(get_conversational_goal(session_id=session_id)),
            "collaborative_reasoning": True,
        },
        "resume_preview": resume.get("resume_text", "")[:300],
        "autonomous_execution_blocked": True,
    }


def clear_conversation_for_tests() -> None:
    from aethos_core.conversation.operational_memory import clear_operational_memory_for_tests
    from aethos_core.human_centered.continuity_memory import clear_continuity_memory_for_tests
    from aethos_core.tenancy.tenant_data_store import clear_namespace, reset_for_tests

    root = _conv_root()
    for p in root.glob("*.json"):
        p.unlink()
    clear_namespace(_NS_THREADS)
    clear_namespace(_NS_GOALS)
    reset_for_tests()
    clear_operational_memory_for_tests()
    clear_continuity_memory_for_tests()

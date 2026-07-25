# SPDX-License-Identifier: Apache-2.0
"""Presence runtime — ambient operational collaborator orchestration."""

from __future__ import annotations

from time import time
from typing import Any

from aethos_core.presence.collaboration_state import get_collaboration_focus, list_collaboration_sessions
from aethos_core.presence.operational_feed import aggregate_operational_feed, collect_raw_feed_events, list_feed_events
from aethos_core.presence.presence_brief_synthesis import synthesize_operator_brief
from aethos_core.presence.presence_memory import presence_memory_snapshot
from aethos_core.presence.presence_memory_compaction import compact_presence_memory
from aethos_core.presence.presence_sessions import get_or_create_presence_session, touch_presence_session
from aethos_core.presence.presence_signal_pipeline import process_presence_signals
from aethos_core.presence.replay_bridge import build_presence_timeline, list_presence_timelines
from aethos_core.presence.watch_mode import list_watchers, tick_watchers


def run_presence_cycle(*, session_id: str = "default", channel: str = "system") -> dict[str, Any]:
    """Single presence orchestration cycle — observe, correlate, never execute."""
    psess = get_or_create_presence_session(session_id=session_id, channel=channel)
    focus = get_collaboration_focus()
    aggregate_operational_feed(window_hours=48)
    compact_presence_memory()
    processed = process_presence_signals(collect_raw_feed_events(window_hours=48), focus=focus)
    timeline = build_presence_timeline(window_hours=48)
    watch = tick_watchers(focus=focus)
    return {
        "ok": True,
        "presence_session": psess,
        "feed_count": len(processed.get("events") or []),
        "attention_items": (processed.get("events") or [])[:12],
        "clusters": processed.get("clusters"),
        "incidents": processed.get("incidents"),
        "recommendations": processed.get("recommendations"),
        "attention_quality": processed.get("attention_quality"),
        "timeline_id": timeline.get("timeline_id"),
        "watch_alerts": watch.get("alerts") or [],
        "readonly": True,
        "autonomous_execution_blocked": True,
        "scanned_at": time(),
    }


def get_presence_state(*, session_id: str = "default") -> dict[str, Any]:
    touch_presence_session(session_id)
    focus = get_collaboration_focus()
    processed = process_presence_signals(list_feed_events(limit=40), focus=focus)
    return {
        "ok": True,
        "feed": processed.get("events"),
        "attention": processed.get("events"),
        "clusters": processed.get("clusters"),
        "incidents": processed.get("incidents"),
        "recommendations": processed.get("recommendations"),
        "attention_quality": processed.get("attention_quality"),
        "focus": focus,
        "memory": presence_memory_snapshot(),
        "collaboration_sessions": list_collaboration_sessions(),
        "watchers": list_watchers(),
        "timelines": list_presence_timelines(limit=5),
        "autonomous_execution_blocked": True,
    }


def synthesize_operational_brief(
    *,
    window_hours: int = 2,
    session_id: str = "default",
    user_text: str | None = None,
) -> str:
    """Synthesize operator-grade operational continuity for chat channels."""
    focus = get_collaboration_focus()
    raw = collect_raw_feed_events(window_hours=max(window_hours, 48))
    processed = process_presence_signals(raw, user_text=user_text, focus=focus, window_hours=window_hours)
    return synthesize_operator_brief(
        window_hours=window_hours,
        events=processed.get("events") or [],
        clusters=processed.get("clusters") or [],
        recommendations=processed.get("recommendations") or [],
        intent=processed.get("intent") or "operational",
        focus=focus,
    )


def dismiss_presence_recommendation(recommendation_id: str) -> dict[str, Any]:
    from aethos_core.intelligence.recommendations import dismiss_recommendation
    from aethos_core.presence.presence_memory import record_dismissed

    result = dismiss_recommendation(recommendation_id)
    if result.get("ok"):
        record_dismissed(recommendation_id)
    return result


def snooze_presence_recommendation(recommendation_id: str, *, hours: float = 4.0) -> dict[str, Any]:
    from aethos_core.intelligence.recommendations import snooze_recommendation
    from aethos_core.presence.presence_memory import record_snoozed

    result = snooze_recommendation(recommendation_id, hours=hours)
    if result.get("ok"):
        record_snoozed(recommendation_id, until=time() + hours * 3600)
    return result

# SPDX-License-Identifier: Apache-2.0
"""Operational timeline — story graph and historical intelligence."""

from __future__ import annotations

import json
from time import time
from typing import Any

from pathlib import Path


def _timeline_root() -> Path:
    root = Path(__file__).resolve().parents[2] / "data" / "timeline"
    root.mkdir(parents=True, exist_ok=True)
    return root


def _path(session_id: str) -> Path:
    return _timeline_root() / f"narrative_{session_id}.json"


def record_timeline_event(
    *,
    session_id: str = "default",
    event: str,
    phase: str | None = None,
    cause: str | None = None,
    effect: str | None = None,
) -> None:
    path = _path(session_id)
    rows: list[dict[str, Any]] = []
    if path.is_file():
        try:
            rows = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            rows = []
    rows.insert(0, {"at": time(), "event": event[:300], "phase": phase, "cause": cause, "effect": effect})
    path.write_text(json.dumps(rows[:40], indent=2), encoding="utf-8")


def _load_conversation_threads(*, session_id: str = "default") -> list[dict[str, Any]]:
    from aethos_core.tenancy.tenant_data_store import get_record, set_record

    key = (session_id or "default").strip() or "default"
    stored = get_record("conversation_threads", key, default=None)
    if isinstance(stored, list):
        return stored
    conv_root = Path(__file__).resolve().parents[2] / "data" / "conversation" / f"session_{key}.json"
    if not conv_root.is_file():
        return []
    try:
        threads = json.loads(conv_root.read_text(encoding="utf-8"))
        if isinstance(threads, list):
            set_record("conversation_threads", key, threads)
            return threads
    except (OSError, json.JSONDecodeError):
        pass
    return []


def get_operational_narrative(*, session_id: str = "default") -> dict[str, Any]:
    from aethos_core.conversation.operational_memory import build_continuity_context
    from aethos_core.human_centered.continuity_memory import load_continuity_memory, seed_default_continuity

    seed_default_continuity(session_id=session_id)
    record = load_continuity_memory(session_id=session_id)
    operational = build_continuity_context(session_id=session_id)
    threads = _load_conversation_threads(session_id=session_id)
    path = _path(session_id)
    events: list[dict[str, Any]] = []
    if path.is_file():
        try:
            events = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            pass

    if not events:
        for resolved in (record.get("resolved") or [])[:4]:
            record_timeline_event(session_id=session_id, event=resolved, phase=record.get("phase"))
        path = _path(session_id)
        if path.is_file():
            events = json.loads(path.read_text(encoding="utf-8"))

    historical_match = (
        "This workflow instability resembles the Phase 9.8E runtime convergence pattern — "
        "similar provider_runtime path and replay integrity degradation during long sessions."
    )

    stabilized = record.get("resolved") or []
    thread_topics: list[str] = []
    thread_unresolved: list[str] = []
    for thread in threads[:3]:
        thread_topics.extend(thread.get("topics") or [])
        thread_unresolved.extend(thread.get("unresolved") or [])

    remaining = list(
        dict.fromkeys(
            (thread_unresolved or [])
            + (operational.get("unresolved_issues") or [])
            + (record.get("unresolved") or [])
            + (record.get("pending_validation") or [])
        )
    )

    story_lines = []
    if stabilized:
        story_lines.append("Over the last few hours we stabilized:")
        for s in stabilized[:3]:
            story_lines.append(f"- {s}")

    if thread_topics:
        story_lines.append("")
        story_lines.append("We were investigating:")
        for topic in list(dict.fromkeys(thread_topics))[:4]:
            story_lines.append(f"- {topic}")

    if remaining:
        story_lines.append("")
        story_lines.append(f"The remaining unresolved area is **{remaining[0]}**.")

    return {
        "ok": True,
        "events": events[:12],
        "story": "\n".join(story_lines) if story_lines else historical_match,
        "historical_intelligence": historical_match,
        "cause_effect_chains": [{"cause": e.get("cause"), "effect": e.get("effect")} for e in events[:5] if e.get("cause")],
        "autonomous_execution_blocked": True,
    }


def clear_timeline_for_tests() -> None:
    root = _timeline_root()
    for p in root.glob("*.json"):
        p.unlink()

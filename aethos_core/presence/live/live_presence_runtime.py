# SPDX-License-Identifier: Apache-2.0
"""Live presence runtime — realtime operational awareness."""

from __future__ import annotations

import json
from time import time
from typing import Any

from pathlib import Path


def _live_root() -> Path:
    root = Path(__file__).resolve().parents[3] / "data" / "presence" / "live"
    root.mkdir(parents=True, exist_ok=True)
    return root


def _focus_path(session_id: str) -> Path:
    return _live_root() / f"focus_{session_id}.json"


def record_focus(*, session_id: str = "default", topic: str, duration_minutes: float = 0) -> None:
    path = _focus_path(session_id)
    record = {"topic": topic, "started_at": time(), "duration_minutes": duration_minutes}
    if path.is_file():
        try:
            prev = json.loads(path.read_text(encoding="utf-8"))
            elapsed = (time() - float(prev.get("started_at", time()))) / 60
            record["duration_minutes"] = round(elapsed, 1)
        except (OSError, json.JSONDecodeError):
            pass
    path.write_text(json.dumps(record, indent=2), encoding="utf-8")


def get_live_focus(*, session_id: str = "default") -> dict[str, Any]:
    path = _focus_path(session_id)
    if not path.is_file():
        return {"topic": None, "duration_minutes": 0}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        elapsed = (time() - float(data.get("started_at", time()))) / 60
        return {"topic": data.get("topic"), "duration_minutes": round(elapsed, 1)}
    except (OSError, json.JSONDecodeError):
        return {"topic": None, "duration_minutes": 0}


def build_contextual_nudge(*, session_id: str = "default") -> dict[str, Any]:
    """Calm recommendation based on continuity memory and live focus."""
    from aethos_core.conversation.continuity_renderer import render_continuity_resume
    from aethos_core.human_centered.continuity_memory import load_continuity_memory, seed_default_continuity
    from aethos_core.presence.presence_runtime import run_presence_cycle

    seed_default_continuity(session_id=session_id)
    record = load_continuity_memory(session_id=session_id)
    focus = get_live_focus(session_id=session_id)
    cycle = run_presence_cycle(session_id=session_id, channel="live")
    rendered = render_continuity_resume(session_id=session_id, lookback_hours=4)

    next_step = record.get("next_best_step") or "Validate Living Companion and Runtime Integrity panels"
    options: list[str] = [
        "investigate route registration",
        "generate a governed patch proposal",
        "replay the runtime integrity chain",
        "open a collaboration room",
    ]
    tl = " ".join([str(record.get("focus") or ""), str(record.get("current_system_focus") or "")]).lower()
    if "deploy" in tl or "railway" in tl:
        options = [
            "latest deployment timeline",
            "correlated workflow failures",
            "a governed patch proposal",
            "recovery replay walkthrough",
        ]

    lines = [rendered.get("resume_core", rendered.get("resume_text", ""))[:600], "", "Would you like me to:"]
    for o in options[:4]:
        lines.append(f"- {o}")
    lines.append("")
    lines.append(f"*Next best step: {next_step}*")

    message = "\n".join(lines)
    return {
        "ok": True,
        "nudge": message,
        "focus": focus,
        "continuity": record,
        "options": options[:4],
        "next_best_step": next_step,
        "interruption_budget_remaining": 3,
        "explainability": rendered.get("explainability"),
        "readonly": True,
        "autonomous_execution_blocked": True,
    }


def get_live_operational_stream(*, session_id: str = "default", limit: int = 20) -> dict[str, Any]:
    from aethos_core.presence.presence_runtime import get_presence_state, run_presence_cycle

    cycle = run_presence_cycle(session_id=session_id, channel="live")
    state = get_presence_state(session_id=session_id)
    return {
        "ok": True,
        "stream": (cycle.get("attention_items") or [])[:limit],
        "clusters": cycle.get("clusters"),
        "incidents": cycle.get("incidents"),
        "environment": {
            "focus": state.get("focus"),
            "collaboration_sessions": state.get("collaboration_sessions"),
            "watchers": state.get("watchers"),
        },
        "live_focus": get_live_focus(session_id=session_id),
        "readonly": True,
        "autonomous_execution_blocked": True,
        "streamed_at": time(),
    }


def get_live_presence_status(*, session_id: str = "default") -> dict[str, Any]:
    return {
        "ok": True,
        "phase": "10.1A",
        "features": {
            "live_operational_stream": True,
            "active_collaboration_sessions": True,
            "live_environment_awareness": True,
            "realtime_focus_tracking": True,
            "adaptive_interruption_timing": True,
            "contextual_nudge_engine": True,
            "temporal_memory_continuity": True,
        },
        "focus": get_live_focus(session_id=session_id),
        "autonomous_execution_blocked": True,
    }


def clear_live_presence_for_tests() -> None:
    root = _live_root()
    for p in root.glob("focus_*.json"):
        p.unlink()

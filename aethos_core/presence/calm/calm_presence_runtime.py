# SPDX-License-Identifier: Apache-2.0
"""Calm presence runtime — interruption budgeting and focus protection."""

from __future__ import annotations

import json
from time import time
from typing import Any

from pathlib import Path


def _calm_root() -> Path:
    root = Path(__file__).resolve().parents[3] / "data" / "presence" / "calm"
    root.mkdir(parents=True, exist_ok=True)
    return root


def _path(session_id: str) -> Path:
    return _calm_root() / f"calm_{session_id}.json"


def get_calm_presence_state(*, session_id: str = "default") -> dict[str, Any]:
    from aethos_core.presence.interruption_policy import interruption_stats
    from aethos_core.presence.live.live_presence_runtime import get_live_focus

    focus = get_live_focus(session_id=session_id)
    stats = interruption_stats()
    minutes = float(focus.get("duration_minutes") or 0)
    budget = 3
    path = _path(session_id)
    if path.is_file():
        try:
            budget = int(json.loads(path.read_text()).get("interruption_budget_remaining", 3))
        except (OSError, json.JSONDecodeError):
            pass

    quiet = minutes >= 90
    return {
        "ok": True,
        "phase": "10.1.3B",
        "features": {
            "interruption_budgeting": True,
            "emotional_pacing": True,
            "urgency_decay": True,
            "recommendation_cooldowns": True,
            "quiet_mode_awareness": quiet,
            "focus_protection": minutes >= 60,
        },
        "interruption_budget_remaining": budget,
        "quiet_mode_recommended": quiet,
        "should_interrupt": not quiet or budget > 0,
        "focus_minutes": minutes,
        "suppressed_count": int(stats.get("suppressed") or 0),
        "autonomous_execution_blocked": True,
    }


def consume_interruption_budget(*, session_id: str = "default") -> dict[str, Any]:
    state = get_calm_presence_state(session_id=session_id)
    remaining = max(0, int(state.get("interruption_budget_remaining", 3)) - 1)
    _path(session_id).write_text(json.dumps({"interruption_budget_remaining": remaining, "at": time()}, indent=2))
    return {"ok": True, "interruption_budget_remaining": remaining}


def clear_calm_presence_for_tests() -> None:
    root = _calm_root()
    for p in root.glob("*.json"):
        p.unlink()

# SPDX-License-Identifier: Apache-2.0
"""Recovery history — prior stabilization outcomes."""

from __future__ import annotations

from typing import Any

from aethos_core.recovery_orchestration.recovery_memory import recovery_memory_state


def recovery_history_state() -> dict[str, Any]:
    mem = recovery_memory_state()
    successes = sum(1 for p in mem.get("patterns") or [] if p.get("escalation") == "normal")
    return {
        "patterns": mem.get("patterns") or [],
        "count": mem.get("count", 0),
        "success_rate": round(successes / max(len(mem.get("patterns") or []), 1), 2),
        "summary": f"Recovery history: {mem.get('count', 0)} patterns recorded.",
    }

# SPDX-License-Identifier: Apache-2.0
"""Verification decay — confidence degradation over time."""

from __future__ import annotations

from typing import Any


def assess_verification_decay(*, supervision: dict[str, Any], memory_events: list[dict[str, Any]]) -> dict[str, Any]:
    loops = supervision.get("restart_patterns", {}).get("restart_loops_detected", 0)
    recurring = sum(1 for e in memory_events if e.get("restart_loops", 0) > 0)
    decay = min(0.35, loops * 0.08 + recurring * 0.05)
    return {
        "verification_decay": round(decay, 2),
        "confidence_retained": decay < 0.15,
        "summary": "Verification confidence stable." if decay < 0.15 else "Verification confidence degrading — extended rechecks active.",
    }

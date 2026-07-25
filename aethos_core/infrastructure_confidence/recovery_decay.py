# SPDX-License-Identifier: Apache-2.0
"""Recovery decay — stabilization confidence over time."""

from __future__ import annotations

from typing import Any


def assess_recovery_decay(*, supervision: dict[str, Any]) -> dict[str, Any]:
    loops = supervision.get("restart_patterns", {}).get("restart_loops_detected", 0)
    decay = min(0.4, loops * 0.1)
    return {"recovery_decay": round(decay, 2), "confidence_retained": decay < 0.2}

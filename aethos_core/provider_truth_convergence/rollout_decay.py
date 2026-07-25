# SPDX-License-Identifier: Apache-2.0
"""Rollout decay — rollout degradation detection."""

from __future__ import annotations

from typing import Any


def detect_rollout_decay(*, initial_healthy: bool = True, decay_detected: bool = False) -> dict[str, Any]:
    return {
        "rollout_stable": initial_healthy and not decay_detected,
        "decay_detected": decay_detected,
        "summary": "Rollout degradation detected — topology recovery monitoring active."
        if decay_detected
        else "Rollout stability maintained within monitoring window.",
    }

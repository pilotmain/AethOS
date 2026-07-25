# SPDX-License-Identifier: Apache-2.0
"""Continuity decay detection — post-recovery erosion."""

from __future__ import annotations

from typing import Any

from aethos_core.recovery_convergence.recovery_decay_detection import detect_recovery_decay


def detect_continuity_decay() -> dict[str, Any]:
    decay = detect_recovery_decay()
    bounded = decay.get("post_rollback_stable", decay.get("stable", True))
    return {
        **decay,
        "continuity_erosion": not bounded,
        "summary": "Post-recovery erosion bounded within acceptable limits." if bounded else "Post-recovery erosion detected — continuity monitoring active.",
    }

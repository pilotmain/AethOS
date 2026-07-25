# SPDX-License-Identifier: Apache-2.0
"""Replay erosion — replay degradation."""

from __future__ import annotations

from typing import Any

from aethos_core.sustained_verification.verification_decay import assess_verification_decay


def assess_replay_erosion() -> dict[str, Any]:
    decay = assess_verification_decay(base=0.85, hours=4.0)
    return {
        **decay,
        "replay_eroding": not decay.get("erosion_bounded", True),
        "summary": "Replay continuity erosion detected." if not decay.get("erosion_bounded") else "Replay erosion bounded.",
    }

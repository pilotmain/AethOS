# SPDX-License-Identifier: Apache-2.0
"""Trust decay runtime — confidence erosion."""

from __future__ import annotations

from typing import Any

from aethos_core.long_tail_operational_decay.temporal_operational_decay import assess_temporal_operational_decay


def assess_trust_decay(*, hours: float = 6.0) -> dict[str, Any]:
    decay = assess_temporal_operational_decay(hours=hours)
    return {
        **decay,
        "trust_erosion_bounded": decay.get("decay_bounded", True),
        "summary": "Temporal trust erosion bounded." if decay.get("decay_bounded") else "Trust erosion detected — adaptive verification active.",
    }

# SPDX-License-Identifier: Apache-2.0
"""Degradation resilience — erosion resistance."""

from __future__ import annotations

from typing import Any

from aethos_core.long_tail_operational_decay.temporal_operational_decay import assess_temporal_operational_decay


def assess_degradation_resilience(*, hours: float = 8.0) -> dict[str, Any]:
    decay = assess_temporal_operational_decay(hours=hours)
    resistant = decay.get("decay_bounded", True)
    return {
        **decay,
        "erosion_resistant": resistant,
        "summary": "Degradation resistance held across long-tail windows." if resistant else "Degradation resilience monitoring active.",
    }

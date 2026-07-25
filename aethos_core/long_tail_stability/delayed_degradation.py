# SPDX-License-Identifier: Apache-2.0
"""Delayed degradation — long-tail erosion."""

from __future__ import annotations

from typing import Any

from aethos_core.long_tail_operational_decay.temporal_operational_decay import assess_temporal_operational_decay


def detect_delayed_degradation(*, hours: float = 8.0) -> dict[str, Any]:
    return assess_temporal_operational_decay(hours=hours)

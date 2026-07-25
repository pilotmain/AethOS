# SPDX-License-Identifier: Apache-2.0
"""Temporal decay — long-tail confidence erosion."""

from __future__ import annotations

from typing import Any

from aethos_core.production_execution_truth.operational_decay import assess_operational_decay


def assess_temporal_decay(*, hours: float = 6.0) -> dict[str, Any]:
    return assess_operational_decay(base_confidence=0.85, hours_elapsed=hours)

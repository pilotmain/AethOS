# SPDX-License-Identifier: Apache-2.0
"""Temporal operational decay — long-tail degradation."""

from __future__ import annotations

from typing import Any

from aethos_core.runtime_decay.temporal_decay import assess_temporal_decay


def assess_temporal_operational_decay(*, hours: float = 8.0) -> dict[str, Any]:
    return assess_temporal_decay(hours=hours)

# SPDX-License-Identifier: Apache-2.0
"""Acceleration memory — instability acceleration history."""

from __future__ import annotations

from typing import Any

from aethos_core.fragility_acceleration.acceleration_memory import record_acceleration_memory


def record_degradation_acceleration_memory(*, zone: str = "degradation_edge") -> dict[str, Any]:
    return record_acceleration_memory(zone=zone)

# SPDX-License-Identifier: Apache-2.0
"""Acceleration memory — fragility escalation history."""

from __future__ import annotations

from typing import Any

from aethos_core.infrastructure_fragility.fragility_memory import record_fragility_memory


def record_acceleration_memory(*, zone: str = "predictive_edge") -> dict[str, Any]:
    return record_fragility_memory(zone=zone)

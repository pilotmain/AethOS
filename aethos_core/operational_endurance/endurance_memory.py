# SPDX-License-Identifier: Apache-2.0
"""Endurance memory — endurance trajectory history."""

from __future__ import annotations

from typing import Any

from aethos_core.operational_fatigue_cognition.fatigue_memory import record_fatigue_trajectory


def record_endurance_memory(*, stable: bool = True) -> dict[str, Any]:
    return record_fatigue_trajectory(score=0.33 if stable else 0.72)

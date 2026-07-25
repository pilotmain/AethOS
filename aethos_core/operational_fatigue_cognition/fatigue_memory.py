# SPDX-License-Identifier: Apache-2.0
"""Fatigue memory — fatigue trajectory history."""

from __future__ import annotations

from typing import Any

from aethos_core.operational_fatigue_intelligence.fatigue_memory import record_fatigue_memory


def record_fatigue_trajectory(*, score: float = 0.34) -> dict[str, Any]:
    return record_fatigue_memory(score=score)

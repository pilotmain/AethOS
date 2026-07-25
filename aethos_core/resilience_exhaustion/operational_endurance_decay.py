# SPDX-License-Identifier: Apache-2.0
"""Operational endurance decay — runtime endurance weakening."""

from __future__ import annotations

from typing import Any

from aethos_core.operational_fatigue_cognition.operational_exhaustion import assess_operational_exhaustion


def assess_operational_endurance_decay() -> dict[str, Any]:
    decay = assess_operational_exhaustion()
    return {
        **decay,
        "endurance_weakening": decay.get("accelerating", False),
        "summary": "Operational endurance decay within durable bounds.",
    }

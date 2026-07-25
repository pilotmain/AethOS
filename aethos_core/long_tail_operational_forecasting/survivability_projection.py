# SPDX-License-Identifier: Apache-2.0
"""Survivability projection — durability forecasting."""

from __future__ import annotations

from typing import Any

from aethos_core.sustained_stability_forecasting.resilience_decay_projection import project_resilience_decay


def project_survivability(*, hours: float = 8.0) -> dict[str, Any]:
    decay = project_resilience_decay(hours=hours)
    return {
        **decay,
        "survivable": decay.get("erosion_resistant", True),
        "summary": "Long-tail survivability projection within durable bounds.",
    }

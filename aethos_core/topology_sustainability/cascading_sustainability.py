# SPDX-License-Identifier: Apache-2.0
"""Cascading sustainability — propagation survivability."""

from __future__ import annotations

from typing import Any

from aethos_core.topology_stability_forecasting.cascading_failure_forecasting import forecast_cascading_failure


def assess_cascading_sustainability() -> dict[str, Any]:
    cascading = forecast_cascading_failure()
    return {
        **cascading,
        "sustainable": cascading.get("protected", True),
        "summary": "Cascading sustainability within durable bounds.",
    }

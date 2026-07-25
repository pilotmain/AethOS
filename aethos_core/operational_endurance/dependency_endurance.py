# SPDX-License-Identifier: Apache-2.0
"""Dependency endurance — dependency survivability."""

from __future__ import annotations

from typing import Any

from aethos_core.topology_fragility_forecasting.dependency_fragility import forecast_dependency_fragility


def assess_dependency_endurance() -> dict[str, Any]:
    dependency = forecast_dependency_fragility()
    return {
        **dependency,
        "enduring": not dependency.get("collapse_risk", False),
        "summary": "Dependency endurance within durable bounds.",
    }

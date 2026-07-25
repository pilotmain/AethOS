# SPDX-License-Identifier: Apache-2.0
"""Dependency survivability — dependency stability."""

from __future__ import annotations

from typing import Any

from aethos_core.topology_fragility_forecasting.dependency_fragility import forecast_dependency_fragility


def assess_dependency_survivability() -> dict[str, Any]:
    dep = forecast_dependency_fragility()
    return {
        **dep,
        "survivable": not dep.get("collapse_risk", False),
        "summary": "Dependency survivability within durable bounds." if not dep.get("collapse_risk") else "Dependency survivability monitoring active.",
    }

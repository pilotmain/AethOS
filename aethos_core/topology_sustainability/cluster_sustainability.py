# SPDX-License-Identifier: Apache-2.0
"""Cluster sustainability — cluster survivability."""

from __future__ import annotations

from typing import Any

from aethos_core.topology_stability_forecasting.cluster_pressure_forecasting import forecast_cluster_pressure


def assess_cluster_sustainability() -> dict[str, Any]:
    cluster = forecast_cluster_pressure()
    return {
        **cluster,
        "sustainable": cluster.get("resilient", True),
        "summary": "Cluster sustainability within durable bounds.",
    }

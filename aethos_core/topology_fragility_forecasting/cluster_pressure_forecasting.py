# SPDX-License-Identifier: Apache-2.0
"""Cluster pressure forecasting — cluster stress prediction."""

from __future__ import annotations

from typing import Any

from aethos_core.topology_stability_forecasting.cluster_pressure_forecasting import forecast_cluster_pressure


def forecast_cluster_pressure_escalation() -> dict[str, Any]:
    return forecast_cluster_pressure()

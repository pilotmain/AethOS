# SPDX-License-Identifier: Apache-2.0
"""Topology stability forecasting aggregate."""

from __future__ import annotations

from typing import Any

from aethos_core.topology_stability_forecasting.topology_runtime import orchestrate_topology_forecast


def assess_topology_stability_forecasting() -> dict[str, Any]:
    forecast = orchestrate_topology_forecast()
    return {"ok": True, **forecast}

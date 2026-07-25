# SPDX-License-Identifier: Apache-2.0
"""Topology fragility forecasting aggregate."""

from __future__ import annotations

from typing import Any

from aethos_core.topology_fragility_forecasting.topology_runtime import orchestrate_topology_fragility


def assess_topology_fragility_forecasting() -> dict[str, Any]:
    forecast = orchestrate_topology_fragility()
    return {"ok": True, **forecast}

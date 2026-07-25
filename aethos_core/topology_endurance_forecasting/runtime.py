# SPDX-License-Identifier: Apache-2.0
"""Topology endurance forecasting aggregate."""

from __future__ import annotations

from typing import Any

from aethos_core.topology_endurance_forecasting.topology_runtime import orchestrate_topology_endurance


def assess_topology_endurance_forecasting() -> dict[str, Any]:
    topology = orchestrate_topology_endurance()
    return {"ok": True, **topology}

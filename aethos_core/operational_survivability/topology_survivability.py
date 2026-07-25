# SPDX-License-Identifier: Apache-2.0
"""Topology survivability — topology endurance."""

from __future__ import annotations

from typing import Any

from aethos_core.long_tail_operational_forecasting.topology_sustainability_projection import project_topology_sustainability


def assess_topology_survivability() -> dict[str, Any]:
    return project_topology_sustainability()

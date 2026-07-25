# SPDX-License-Identifier: Apache-2.0
"""Topology erosion — topology collapse."""

from __future__ import annotations

from typing import Any

from aethos_core.runtime_decay.topology_pressure import assess_topology_pressure


def assess_topology_erosion() -> dict[str, Any]:
    return assess_topology_pressure()

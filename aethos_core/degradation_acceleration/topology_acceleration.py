# SPDX-License-Identifier: Apache-2.0
"""Topology acceleration — topology instability momentum."""

from __future__ import annotations

from typing import Any

from aethos_core.fragility_acceleration.topology_acceleration import detect_topology_acceleration


def measure_topology_acceleration() -> dict[str, Any]:
    return detect_topology_acceleration()

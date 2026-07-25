# SPDX-License-Identifier: Apache-2.0
"""Topology weakening — topology fragility growth."""

from __future__ import annotations

from typing import Any

from aethos_core.predictive_operational_cognition.topology_projection import project_topology_stability


def detect_topology_weakening() -> dict[str, Any]:
    return project_topology_stability()

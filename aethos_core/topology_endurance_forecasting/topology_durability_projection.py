# SPDX-License-Identifier: Apache-2.0
"""Topology durability projection — topology endurance."""

from __future__ import annotations

from typing import Any

from aethos_core.runtime_survivability_intelligence.topology_survivability_projection import project_topology_survivability


def project_topology_durability() -> dict[str, Any]:
    return project_topology_survivability()

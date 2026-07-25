# SPDX-License-Identifier: Apache-2.0
"""Topology weakening — topology degradation."""

from __future__ import annotations

from typing import Any

from aethos_core.runtime_fragility_intelligence.topology_fragility_projection import project_topology_fragility


def detect_topology_degradation() -> dict[str, Any]:
    return project_topology_fragility()

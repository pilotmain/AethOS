# SPDX-License-Identifier: Apache-2.0
"""Topology trust — topology durability confidence."""

from __future__ import annotations

from typing import Any

from aethos_core.temporal_trust_evolution.topology_stability_confidence import assess_topology_stability_confidence


def assess_topology_durability_trust() -> dict[str, Any]:
    return assess_topology_stability_confidence()

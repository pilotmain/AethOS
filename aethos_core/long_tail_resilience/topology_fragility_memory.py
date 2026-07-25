# SPDX-License-Identifier: Apache-2.0
"""Topology fragility memory — topology weak points."""

from __future__ import annotations

from typing import Any

from aethos_core.long_tail_resilience_memory.topology_fragility_memory import recall_topology_fragility_memory


def recall_topology_weak_points(*, fragility_score: float = 0.22) -> dict[str, Any]:
    return recall_topology_fragility_memory(fragility_score=fragility_score)

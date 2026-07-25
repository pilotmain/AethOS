# SPDX-License-Identifier: Apache-2.0
"""Topology memory — dependency weak points."""

from __future__ import annotations

from typing import Any

from aethos_core.infrastructure_intuition.topology_fragility import detect_topology_fragility


def recall_topology_memory(*, fragility_score: float = 0.28) -> dict[str, Any]:
    return detect_topology_fragility(fragility_score=fragility_score)

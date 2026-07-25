# SPDX-License-Identifier: Apache-2.0
"""Topology fragility memory — weak topology zones."""

from __future__ import annotations

from typing import Any

from aethos_core.long_tail_operational_memory.topology_memory import recall_topology_memory


def recall_topology_fragility_memory(*, fragility_score: float = 0.24) -> dict[str, Any]:
    return recall_topology_memory(fragility_score=fragility_score)

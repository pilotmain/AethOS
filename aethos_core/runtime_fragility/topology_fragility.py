# SPDX-License-Identifier: Apache-2.0
"""Topology fragility — weak topology zones."""

from __future__ import annotations

from typing import Any

from aethos_core.infrastructure_fragility.topology_fragility_runtime import assess_topology_fragility_runtime


def detect_topology_fragility() -> dict[str, Any]:
    return assess_topology_fragility_runtime()

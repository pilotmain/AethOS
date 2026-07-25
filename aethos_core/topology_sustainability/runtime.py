# SPDX-License-Identifier: Apache-2.0
"""Topology sustainability aggregate."""

from __future__ import annotations

from typing import Any

from aethos_core.topology_sustainability.topology_runtime import orchestrate_topology_sustainability


def assess_topology_sustainability() -> dict[str, Any]:
    topology = orchestrate_topology_sustainability()
    return {"ok": True, **topology}

# SPDX-License-Identifier: Apache-2.0
"""Mesh resilience — service mesh recovery."""

from __future__ import annotations

from typing import Any

from aethos_core.kubernetes_convergence.service_mesh_recovery import assess_service_mesh_recovery


def assess_mesh_resilience() -> dict[str, Any]:
    mesh = assess_service_mesh_recovery(routes_healthy=True)
    return {**mesh, "resilient": mesh.get("routes_healthy", False)}

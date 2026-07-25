# SPDX-License-Identifier: Apache-2.0
"""Mesh instability projection — service mesh degradation."""

from __future__ import annotations

from typing import Any

from aethos_core.topology_stability_forecasting.mesh_instability_projection import project_mesh_instability


def project_mesh_degradation() -> dict[str, Any]:
    return project_mesh_instability()

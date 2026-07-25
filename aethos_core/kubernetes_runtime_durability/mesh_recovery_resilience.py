# SPDX-License-Identifier: Apache-2.0
"""Mesh recovery resilience — service mesh durability."""

from __future__ import annotations

from typing import Any

from aethos_core.kubernetes_resilience.mesh_resilience import assess_mesh_resilience


def assess_mesh_recovery_resilience() -> dict[str, Any]:
    return assess_mesh_resilience()

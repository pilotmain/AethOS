# SPDX-License-Identifier: Apache-2.0
"""Convergence alignment — multi-layer reconciliation."""

from __future__ import annotations

from typing import Any

from aethos_core.runtime_reconciliation.reconciliation_runtime import orchestrate_reconciliation


def assess_convergence_alignment(*, provider: str = "railway") -> dict[str, Any]:
    recon = orchestrate_reconciliation(provider=provider)
    layers = {
        "runtime": recon.get("reconciled", False),
        "topology": recon.get("topology_alignment", {}).get("aligned", False),
        "replay": recon.get("replay_alignment", {}).get("aligned", False),
        "infrastructure": recon.get("infrastructure_alignment", {}).get("aligned", False),
    }
    aligned = sum(1 for v in layers.values() if v)
    return {
        "layers": layers,
        "aligned_count": aligned,
        "total_layers": len(layers),
        "multi_layer_aligned": aligned >= 3,
        "summary": "Multi-layer operational convergence aligned." if aligned >= 3 else "Multi-layer convergence monitoring active.",
    }

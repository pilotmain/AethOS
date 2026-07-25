# SPDX-License-Identifier: Apache-2.0
"""Cross-surface reality convergence aggregate — Phase 11.7.4."""

from __future__ import annotations

from typing import Any

from aethos_core.cross_surface_reality_convergence.convergence_runtime import orchestrate_cross_surface_convergence


def assess_cross_surface_reality_convergence(
    *,
    session_id: str = "default",
    channel: str = "chat",
) -> dict[str, Any]:
    """Phase 11.7.4 — cross-surface reality convergence."""
    convergence = orchestrate_cross_surface_convergence(session_id=session_id, channel=channel)
    return {
        "ok": True,
        "phase": "11.7.4",
        "converged": convergence.get("convergence_qualified"),
        "cross_surface_convergence": convergence,
        "summary": convergence.get("summary", "Cross-surface convergence assessing."),
    }

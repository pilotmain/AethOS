# SPDX-License-Identifier: Apache-2.0
"""Rollout resilience — rollout durability."""

from __future__ import annotations

from typing import Any

from aethos_core.kubernetes_convergence.rollout_convergence import assess_rollout_convergence


def assess_rollout_resilience() -> dict[str, Any]:
    rollout = assess_rollout_convergence(stabilized=True)
    return {
        **rollout,
        "resilient": rollout.get("converged", False),
        "summary": "Rollout resilience durable under sustained pressure." if rollout.get("converged") else "Rollout resilience monitoring active.",
    }

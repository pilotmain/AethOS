# SPDX-License-Identifier: Apache-2.0
"""Kubernetes rollout convergence — rollout recovery."""

from __future__ import annotations

from typing import Any

from aethos_core.provider_truth_convergence.kubernetes_rollout_truth import assess_kubernetes_rollout_truth


def assess_kubernetes_rollout_convergence() -> dict[str, Any]:
    truth = assess_kubernetes_rollout_truth()
    return {**truth, "converged": truth.get("rollout_stabilized", False)}

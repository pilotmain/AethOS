# SPDX-License-Identifier: Apache-2.0
"""Kubernetes topology truth — rollout stabilization."""

from __future__ import annotations

from typing import Any

from aethos_core.provider_runtime_truth.kubernetes_rollout_convergence import assess_kubernetes_rollout_convergence


def assess_kubernetes_topology_truth() -> dict[str, Any]:
    return assess_kubernetes_rollout_convergence()

# SPDX-License-Identifier: Apache-2.0
"""Namespace resilience — namespace stability."""

from __future__ import annotations

from typing import Any

from aethos_core.kubernetes_convergence.namespace_stability import assess_namespace_stability


def assess_namespace_resilience() -> dict[str, Any]:
    ns = assess_namespace_stability(healthy=True)
    return {**ns, "resilient": ns.get("healthy", False)}

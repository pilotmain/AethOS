# SPDX-License-Identifier: Apache-2.0
"""Dependency recovery — dependency-aware stabilization."""

from __future__ import annotations

from typing import Any


def plan_dependency_recovery(*, topology: dict[str, Any], plan: dict[str, Any]) -> dict[str, Any]:
    propagation = topology.get("propagation") or {}
    impacted = propagation.get("potentially_impacted") or []
    stages = plan.get("stages") or []
    dependency_order = sorted(stages, key=lambda s: len(impacted) if s.get("service") in impacted else 0)
    return {
        "dependency_aware_order": dependency_order,
        "impacted_services": impacted,
        "summary": "Dependency-aware recovery sequencing applied.",
    }

# SPDX-License-Identifier: Apache-2.0
"""Dependency weighting — critical-path confidence."""

from __future__ import annotations

from typing import Any


def weight_dependency_confidence(*, topology: dict[str, Any], docker: dict[str, Any]) -> dict[str, Any]:
    critical = topology.get("classifications", {}).get("critical") or []
    pressure = docker.get("pressure", {}).get("elevated_count", 0)
    weight = max(0.3, 1.0 - pressure * 0.1)
    return {
        "critical_path_count": len(critical),
        "dependency_confidence": round(weight, 2),
    }

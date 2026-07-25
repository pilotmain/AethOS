# SPDX-License-Identifier: Apache-2.0
"""Degraded pathways — fallback operational paths."""

from __future__ import annotations

from typing import Any


def identify_degraded_pathways(*, escalation: dict[str, Any]) -> dict[str, Any]:
    if escalation.get("escalate"):
        pathways = [
            {"path": "readonly_mode", "available": True},
            {"path": "reduced_topology", "available": True},
            {"path": "manual_governance", "available": True},
        ]
    else:
        pathways = [{"path": "normal_operations", "available": True}]
    return {
        "pathways": pathways,
        "fallback_active": escalation.get("escalate", False),
        "summary": "Fallback operational pathways identified." if escalation.get("escalate") else "Normal operational pathway active.",
    }

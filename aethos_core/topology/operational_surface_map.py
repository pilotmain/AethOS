# SPDX-License-Identifier: Apache-2.0
"""Operational surface map — infrastructure visualization metadata."""

from __future__ import annotations

from typing import Any


def build_operational_surface_map(*, graph: dict[str, Any], classifications: dict[str, Any]) -> dict[str, Any]:
    layers = {
        "edge": [n for n in (graph.get("nodes") or []) if isinstance(n, dict) and "ingress" in str(n.get("id", ""))],
        "core": [{"id": s} for s in classifications.get("critical") or []],
        "supporting": [{"id": s} for s in classifications.get("supporting") or []],
    }
    return {
        "layers": layers,
        "visualization_ready": graph.get("node_count", 0) > 0,
        "summary": "Operational surface map ready for Mission Control visualization.",
    }

# SPDX-License-Identifier: Apache-2.0
"""Resource exhaustion — CPU/memory leak analysis."""

from __future__ import annotations

from typing import Any


def analyze_resource_exhaustion(*, runtime_snapshot: dict[str, Any]) -> dict[str, Any]:
    workloads = runtime_snapshot.get("containers") or runtime_snapshot.get("pods") or []
    if not isinstance(workloads, list):
        workloads = []
    exhausted = [
        w for w in workloads
        if isinstance(w, dict) and str(w.get("memory_pressure") or w.get("cpu_pressure") or "").lower() in ("elevated", "high", "critical")
    ]
    return {
        "exhaustion_signals": len(exhausted),
        "workloads": [w.get("name") for w in exhausted],
        "summary": f"{len(exhausted)} workloads report resource exhaustion signals." if exhausted else "No resource exhaustion detected.",
    }

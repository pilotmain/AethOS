# SPDX-License-Identifier: Apache-2.0
"""Runtime pressure — CPU/memory/runtime pressure."""

from __future__ import annotations

from typing import Any


def assess_runtime_pressure(*, runtime_snapshot: dict[str, Any], containers: list[dict[str, Any]]) -> dict[str, Any]:
    elevated: list[dict[str, Any]] = []
    for c in containers:
        pressure = str(c.get("memory_pressure") or c.get("cpu_pressure") or "").lower()
        if pressure in ("elevated", "high", "critical"):
            elevated.append({"name": c.get("name"), "pressure": pressure})
    global_pressure = str(runtime_snapshot.get("cluster_pressure") or "").lower()
    return {
        "elevated_containers": elevated,
        "elevated_count": len(elevated),
        "cluster_pressure": global_pressure or "normal",
        "summary": (
            f"{len(elevated)} containers report elevated runtime pressure."
            if elevated
            else "Runtime pressure within expected thresholds."
        ),
    }

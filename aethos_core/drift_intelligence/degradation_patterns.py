# SPDX-License-Identifier: Apache-2.0
"""Degradation patterns — recurring instability detection."""

from __future__ import annotations

from typing import Any


def detect_degradation_patterns(*, supervision: dict[str, Any], memory: dict[str, Any]) -> dict[str, Any]:
    loops = supervision.get("restart_patterns", {}).get("unstable_workloads") or []
    patterns = memory.get("patterns") or []
    recurring = [p for p in patterns if p.get("degraded")]
    return {
        "unstable_workloads": loops,
        "recurring_patterns": len(recurring),
        "degradation_detected": bool(loops) or len(recurring) > 0,
        "summary": f"{len(loops)} unstable workloads, {len(recurring)} recurring patterns." if loops else "No recurring degradation patterns.",
    }

# SPDX-License-Identifier: Apache-2.0
"""Entropy tracking — operational decay awareness."""

from __future__ import annotations

from typing import Any


def track_operational_entropy(*, infrastructure: dict[str, Any]) -> dict[str, Any]:
    docker = infrastructure.get("docker") or {}
    pressure = docker.get("pressure", {}).get("elevated_count", 0)
    loops = infrastructure.get("supervision", {}).get("restart_patterns", {}).get("restart_loops_detected", 0)
    entropy = min(1.0, (pressure * 0.15) + (loops * 0.12))
    return {
        "entropy_score": round(entropy, 2),
        "elevated": entropy >= 0.25,
        "summary": "Operational entropy within bounds." if entropy < 0.25 else "Operational entropy elevated — drift monitoring active.",
    }

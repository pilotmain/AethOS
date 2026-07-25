# SPDX-License-Identifier: Apache-2.0
"""Runtime watchers — ongoing infrastructure verification."""

from __future__ import annotations

from typing import Any


def watch_runtime_health(*, docker: dict[str, Any], kubernetes: dict[str, Any]) -> dict[str, Any]:
    checks = [
        docker.get("verified"),
        kubernetes.get("verified"),
        docker.get("health", {}).get("all_healthy"),
        kubernetes.get("pods", {}).get("all_ready"),
    ]
    score = sum(1 for c in checks if c) / max(len(checks), 1)
    return {
        "watch_score": round(score, 2),
        "runtime_health_sustained": score >= 0.75,
        "summary": "Runtime health sustained." if score >= 0.75 else "Runtime health requires continued observation.",
    }

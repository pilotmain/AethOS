# SPDX-License-Identifier: Apache-2.0
"""Stabilization confidence — post-recovery confidence."""

from __future__ import annotations

from typing import Any


def score_stabilization_confidence(*, verification: dict[str, Any], recovery: dict[str, Any]) -> dict[str, Any]:
    stabilized = verification.get("stabilization", {}).get("sustained", False)
    coordinated = recovery.get("coordinated", False)
    score = 0.8 if stabilized and coordinated else 0.55 if stabilized else 0.35
    return {
        "stabilization_confidence": round(score, 2),
        "summary": "Post-recovery stabilization confidence high." if score >= 0.7 else "Post-recovery confidence building.",
    }

# SPDX-License-Identifier: Apache-2.0
"""Cluster integrity — cluster operational trust."""

from __future__ import annotations

from typing import Any


def score_cluster_integrity(*, kubernetes: dict[str, Any]) -> dict[str, Any]:
    verified = bool(kubernetes.get("verified"))
    drift = kubernetes.get("drift", {}).get("drift_detected", False)
    score = 0.85 if verified and not drift else 0.55 if verified else 0.35
    return {"cluster_integrity": round(score, 2), "drift_detected": drift}

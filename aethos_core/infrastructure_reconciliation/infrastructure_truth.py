# SPDX-License-Identifier: Apache-2.0
"""Infrastructure truth — runtime operational truth."""

from __future__ import annotations

from typing import Any


def assess_infrastructure_truth(
    *,
    docker: dict[str, Any],
    kubernetes: dict[str, Any],
    reconciliation: dict[str, Any],
) -> dict[str, Any]:
    verified_layers = sum(1 for layer in (docker, kubernetes) if layer.get("verified"))
    reconciled = reconciliation.get("reconciled", False)
    truth_score = (verified_layers / 2) * 0.6 + (0.4 if reconciled else 0.1)
    return {
        "truth_score": round(truth_score, 2),
        "verified_layers": verified_layers,
        "reconciled": reconciled,
        "summary": "Infrastructure operational truth converging." if truth_score >= 0.7 else "Infrastructure truth partially verified.",
    }

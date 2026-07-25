# SPDX-License-Identifier: Apache-2.0
"""Verification confidence — revalidation weighting."""

from __future__ import annotations

from typing import Any


def weight_verification_confidence(*, verification: dict[str, Any]) -> dict[str, Any]:
    coverage = verification.get("verification_coverage_pct", 0) / 100
    decay = verification.get("decay", {}).get("verification_decay", 0)
    score = max(0.0, min(1.0, coverage - decay))
    return {
        "verification_confidence": round(score, 2),
        "summary": "Revalidation weighting supports strong verification confidence." if score >= 0.7 else "Verification confidence moderated by decay.",
    }

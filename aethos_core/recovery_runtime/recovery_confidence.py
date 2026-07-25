# SPDX-License-Identifier: Apache-2.0
"""Recovery confidence — bounded recovery scoring."""

from __future__ import annotations

from typing import Any


def score_recovery_confidence(*, verification: dict[str, Any], reconciliation: dict[str, Any] | None = None) -> dict[str, Any]:
    base = float(verification.get("verification_coverage_pct") or 55) / 100
    if reconciliation and reconciliation.get("reconciled"):
        base = min(0.96, base + 0.08)
    elif reconciliation and not reconciliation.get("reconciled"):
        base = max(0.35, base - 0.12)
    if not verification.get("verified"):
        base = min(base, 0.68)
    return {
        "recovery_confidence": round(base, 2),
        "bounded": True,
        "degraded": base < 0.7,
    }

# SPDX-License-Identifier: Apache-2.0
"""Operational honesty — prevent overstated capability claims."""

from __future__ import annotations

from typing import Any


def assess_operational_honesty(matrix: list[dict[str, Any]]) -> dict[str, Any]:
    """Detect overclaim risk and produce honest operational phrasing."""
    overclaims: list[dict[str, str]] = []
    for row in matrix:
        if not row.get("claimed"):
            continue
        verified = str(row.get("verified") or "none")
        real = str(row.get("real") or "unknown")
        maturity = str(row.get("maturity") or "experimental")
        if verified in ("none", "unknown") and real in ("partial", "full"):
            overclaims.append({
                "capability": str(row.get("name") or row.get("id")),
                "issue": "claimed_without_verification",
                "honest_phrase": (
                    f"{row.get('name')} is available with partial substrate — "
                    "extended verification recommended before declaring full stabilization."
                ),
            })
        elif maturity in ("alpha", "experimental") and row.get("claimed"):
            overclaims.append({
                "capability": str(row.get("name") or row.get("id")),
                "issue": "immature_claim",
                "honest_phrase": (
                    f"{row.get('name')} remains {maturity} — operational proof coverage is incomplete."
                ),
            })

    return {
        "overclaim_count": len(overclaims),
        "overclaim_risk": len(overclaims) > 0,
        "overclaims": overclaims[:12],
        "honesty_principle": (
            "AethOS should never imply more operational certainty than substrate reality supports."
        ),
        "recommended_phrasing": (
            overclaims[0]["honest_phrase"]
            if overclaims
            else "Operational claims align with current verification coverage."
        ),
    }

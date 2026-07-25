# SPDX-License-Identifier: Apache-2.0
"""Maturity classification — honest readiness tiers."""

from __future__ import annotations

MATURITY_TIERS = frozenset({"experimental", "alpha", "beta", "stable", "production-ready"})

TIER_ORDER = ["experimental", "alpha", "beta", "stable", "production-ready"]


def classify_maturity(
    *,
    claimed: bool,
    real_level: str,
    verified_level: str,
    verification_coverage: float,
    prod_ready: bool = False,
) -> str:
    """Map capability signals to maturity tier."""
    if prod_ready and verification_coverage >= 0.9 and verified_level in ("full", "mostly"):
        return "production-ready"
    if verification_coverage >= 0.75 and verified_level in ("full", "mostly", "partial"):
        return "stable"
    if verification_coverage >= 0.5 or verified_level == "partial":
        return "beta"
    if claimed and real_level in ("partial", "full"):
        return "alpha"
    return "experimental"


def tier_label(tier: str) -> str:
    labels = {
        "experimental": "Experimental — conceptual or incomplete",
        "alpha": "Alpha — partial substrate",
        "beta": "Beta — mostly functional",
        "stable": "Stable — operationally reliable",
        "production-ready": "Production-ready — fully verified",
    }
    return labels.get(tier, tier)

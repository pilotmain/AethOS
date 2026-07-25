# SPDX-License-Identifier: Apache-2.0
"""Operational severity scoring for engineering and analyst agents."""

from __future__ import annotations

from typing import Any

SEVERITY_LEVELS = ("LOW", "MEDIUM", "HIGH", "CRITICAL")


def classify_severity(*, signals: list[dict[str, Any]]) -> dict[str, Any]:
    """Score severity from substrate signals — deterministic, no LLM."""
    score = 0
    reasons: list[str] = []
    for sig in signals:
        kind = str(sig.get("kind") or "")
        weight = int(sig.get("weight") or 1)
        detail = str(sig.get("detail") or "")
        if kind == "deployment_failed":
            score += 3 * weight
            reasons.append(detail or "deployment failure detected")
        elif kind == "production_impact":
            score += 4 * weight
            reasons.append(detail or "production impact signal")
        elif kind == "vulnerability":
            score += 2 * weight
            reasons.append(detail or "dependency vulnerability")
        elif kind == "test_failure":
            score += 2 * weight
            reasons.append(detail or "test failures")
        elif kind == "hotspot":
            score += 1 * weight
            reasons.append(detail or "engineering hotspot")
        elif kind == "browser_failure":
            score += 2 * weight
            reasons.append(detail or "browser health failure")
        elif kind == "repeated_failure":
            score += 3 * weight
            reasons.append(detail or "repeated failures")
        elif kind == "missing_verification":
            score += 1 * weight
            reasons.append(detail or "missing verification")

    if score >= 10:
        level = "CRITICAL"
    elif score >= 6:
        level = "HIGH"
    elif score >= 3:
        level = "MEDIUM"
    else:
        level = "LOW"

    return {"severity": level, "score": score, "reasons": reasons[:8]}

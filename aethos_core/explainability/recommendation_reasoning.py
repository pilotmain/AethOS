# SPDX-License-Identifier: Apache-2.0
"""Recommendation reasoning — why a recommendation exists."""

from __future__ import annotations

from typing import Any


def explain_recommendation(rec: dict[str, Any], *, correlation: dict[str, Any] | None = None) -> str:
    parts = [f"Recommendation '{rec.get('title')}' proposed because:"]
    if rec.get("operator_rationale"):
        parts.append(f"- {rec['operator_rationale']}")
    if rec.get("kind"):
        parts.append(f"- Anomaly kind: {rec['kind']}")
    if correlation:
        for c in (correlation.get("correlations") or [])[:2]:
            parts.append(f"- Cross-domain: {c.get('summary')}")
    parts.append("- Human approval required before any execution.")
    return "\n".join(parts)

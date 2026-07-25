# SPDX-License-Identifier: Apache-2.0
"""Confidence reasoning — why confidence changed."""

from __future__ import annotations

from typing import Any


def explain_confidence_change(*, confidence: dict[str, Any], reliability: dict[str, Any] | None = None) -> str:
    parts = ["Confidence bounded because:"]
    for p in confidence.get("penalties") or []:
        parts.append(f"- {p}")
    rel = reliability or {}
    if rel.get("truth_state"):
        parts.append(f"- Truth state: {rel['truth_state']}")
    bounded = confidence.get("bounded_confidence")
    raw = confidence.get("raw_confidence")
    if bounded is not None and raw is not None and bounded < raw:
        parts.append(f"- Adjusted {raw:.2f} → {bounded:.2f} (never report higher than reality).")
    if not confidence.get("penalties"):
        parts.append("- No degradation penalties — confidence within telemetry bounds.")
    return "\n".join(parts)

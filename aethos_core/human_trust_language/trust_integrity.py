# SPDX-License-Identifier: Apache-2.0
"""Trust integrity — prevent overclaiming."""

from __future__ import annotations

from typing import Any

from aethos_core.human_trust.confidence_restraint import should_show_telemetry
from aethos_core.human_trust.trust_calibration import calibrate_trust


def assess_trust_integrity(*, confidence: float, contradictions: int, mode: str) -> dict[str, Any]:
    calibration = calibrate_trust(confidence=confidence, item_count=1, contradictions=contradictions)
    return {
        **calibration,
        "telemetry_allowed": should_show_telemetry(mode=mode),
        "summary": trust_narrative_safe(confidence, contradictions, mode),
    }


def trust_narrative_safe(confidence: float, contradictions: int, mode: str) -> str:
    if should_show_telemetry(mode=mode):
        return f"Confidence {confidence:.2f} with {contradictions} contradiction(s)."
    if contradictions:
        return "These recommendations appeared across several sources, though details varied somewhat."
    return "These recommendations consistently appeared across trusted family and regional sources."

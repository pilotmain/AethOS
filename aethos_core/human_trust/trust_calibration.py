# SPDX-License-Identifier: Apache-2.0
"""Trust calibration — avoid overclaiming."""

from __future__ import annotations

from typing import Any


def calibrate_trust(*, confidence: float, item_count: int, contradictions: int = 0) -> dict[str, Any]:
    overclaim = confidence >= 0.85 and contradictions > 0
    restrained = confidence < 0.9 or contradictions == 0
    return {
        "overclaim_risk": overclaim,
        "restrained": restrained,
        "summary": "Trust calibrated with restraint." if restrained else "Confidence moderated due to source variation.",
    }

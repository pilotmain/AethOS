# SPDX-License-Identifier: Apache-2.0
"""Instability forecasting — future degradation prediction."""

from __future__ import annotations

from typing import Any

from aethos_core.long_tail_stability.delayed_degradation import detect_delayed_degradation


def forecast_instability(*, hours: float = 10.0) -> dict[str, Any]:
    decay = detect_delayed_degradation(hours=hours)
    risk_elevated = not decay.get("decay_bounded", True)
    return {
        **decay,
        "instability_risk_elevated": risk_elevated,
        "summary": "Future instability risk within acceptable bounds." if not risk_elevated else "Future instability risk emerging — predictive monitoring active.",
    }

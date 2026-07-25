# SPDX-License-Identifier: Apache-2.0
"""Recovery risk forecast — recovery failure probability."""

from __future__ import annotations

from typing import Any


def forecast_recovery_risk(*, recovery: dict[str, Any]) -> dict[str, Any]:
    escalate = recovery.get("escalation", {}).get("escalate", False)
    loops = recovery.get("memory", {}).get("count", 0)
    risk = 0.15 + (0.25 if escalate else 0) + min(0.2, loops * 0.02)
    return {
        "recovery_failure_probability": round(min(0.95, risk), 2),
        "summary": f"Recovery failure probability: {round(min(0.95, risk) * 100)}%.",
    }

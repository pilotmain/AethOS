# SPDX-License-Identifier: Apache-2.0
"""Resource exhaustion prediction — pressure forecasting."""

from __future__ import annotations

from typing import Any


def predict_resource_exhaustion(*, infrastructure: dict[str, Any]) -> dict[str, Any]:
    pressure = infrastructure.get("docker", {}).get("pressure", {}).get("elevated_count", 0)
    risk = min(0.9, pressure * 0.2)
    return {
        "exhaustion_risk": round(risk, 2),
        "forecast_horizon_hours": 4,
        "summary": "Resource exhaustion risk elevated." if risk >= 0.3 else "Resource pressure forecast stable.",
    }

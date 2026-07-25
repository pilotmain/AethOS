# SPDX-License-Identifier: Apache-2.0
"""Railway recovery verification — runtime stabilization proof."""

from __future__ import annotations

from typing import Any


def verify_recovery_stabilization(
    *,
    deployment_truth: dict[str, Any],
    health: dict[str, Any],
    telemetry: dict[str, Any],
) -> dict[str, Any]:
    stabilized = (
        deployment_truth.get("stabilized")
        and health.get("health_stabilized")
        and telemetry.get("freshness_recovered")
    )
    return {
        "stabilization_confirmed": stabilized,
        "extended_monitoring_recommended": not stabilized,
        "summary": (
            "Runtime stabilization confirmed."
            if stabilized
            else "Stabilization in progress — extended monitoring remains active."
        ),
    }

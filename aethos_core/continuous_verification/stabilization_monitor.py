# SPDX-License-Identifier: Apache-2.0
"""Stabilization monitor — long-tail recovery observation."""

from __future__ import annotations

from typing import Any


def monitor_stabilization(*, infrastructure: dict[str, Any]) -> dict[str, Any]:
    supervision = infrastructure.get("supervision") or {}
    stabilization = supervision.get("stabilization") or {}
    phase = stabilization.get("stabilization_phase") or "monitoring"
    sustained = phase in ("stabilized", "monitoring") and not supervision.get("restart_patterns", {}).get("anomaly_escalation")
    return {
        "stabilization_phase": phase,
        "sustained": sustained,
        "extended_observation_active": True,
        "summary": "Long-tail stabilization observation active." if not sustained else "Stabilization sustained through extended observation.",
    }

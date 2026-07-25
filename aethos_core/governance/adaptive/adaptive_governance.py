# SPDX-License-Identifier: Apache-2.0
"""Adaptive governance — runtime policy adjustments based on operational reality."""

from __future__ import annotations

from typing import Any

from aethos_core.governance.adaptive.execution_pressure import assess_execution_pressure
from aethos_core.governance.adaptive.governance_memory import governance_memory_snapshot
from aethos_core.governance.adaptive.governance_risk_engine import score_governance_risk
from aethos_core.governance.adaptive.mutation_escalation import assess_mutation_escalation


def assess_adaptive_governance(
    *,
    observations: dict[str, Any] | None = None,
    anomalies: list[dict[str, Any]] | None = None,
    reliability: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Compute adaptive governance posture — dynamic but never self-authorizing."""
    obs = observations or {}
    events = list(obs.get("events") or [])
    memory = governance_memory_snapshot()
    pressure = assess_execution_pressure(events=events)
    risk = score_governance_risk(anomalies=anomalies, pressure=pressure, reliability=reliability)
    escalation = assess_mutation_escalation(
        pressure=pressure,
        validation_successes=int(memory.get("validation_successes") or 0),
    )

    policies: list[str] = []
    if escalation.get("escalated"):
        policies.append("Mutation tier elevated — deeper human approval required.")
    if escalation.get("cooldown_active"):
        policies.append("Restart mutations temporarily restricted after repeated failures.")
    if int(memory.get("validation_successes") or 0) >= 100:
        policies.append("Stability reward active — reduced review friction for validated paths.")
    if risk.get("risk_level") == "high":
        policies.append("High governance risk — preflight scrutiny increased.")

    return {
        **escalation,
        "risk": risk,
        "pressure": pressure,
        "policies": policies,
        "governance_drift": risk.get("risk_level") != "low",
        "readonly": True,
        "autonomous_execution_blocked": True,
    }

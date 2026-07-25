# SPDX-License-Identifier: Apache-2.0
"""Governance reasoning — why approval escalated."""

from __future__ import annotations

from typing import Any


def explain_governance_escalation(governance: dict[str, Any]) -> str:
    parts = ["Governance posture adjusted because:"]
    if governance.get("escalated"):
        parts.append(f"- {governance.get('escalation_reason', 'Mutation tier elevated.')}")
    pressure = governance.get("pressure") or {}
    if int(pressure.get("restart_count") or 0) >= 3:
        parts.append(f"- {pressure['restart_count']} restart attempts in {pressure.get('window_minutes', 30)}m window.")
    if int(pressure.get("workflow_failure_count") or 0) >= 3:
        parts.append(f"- {pressure['workflow_failure_count']} workflow failures detected.")
    if governance.get("cooldown_active"):
        parts.append("- Cooldown active: restart mutations temporarily restricted.")
    risk = governance.get("risk") or {}
    if risk.get("risk_level") == "high":
        parts.append(f"- Governance risk elevated (score={risk.get('risk_score')}).")
    if len(parts) == 1:
        parts.append("- No escalation triggers — baseline governance tier applies.")
    return "\n".join(parts)

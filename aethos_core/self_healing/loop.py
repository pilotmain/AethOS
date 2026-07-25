# SPDX-License-Identifier: Apache-2.0
"""Self-healing operational loop — detect → investigate → verify → learn."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class SelfHealingPlan:
    ok: bool
    stage: str
    summary: str
    proposed_capabilities: list[str] = field(default_factory=list)
    requires_approval: bool = True
    confidence: float = 0.0
    evidence_gaps: list[str] = field(default_factory=list)
    meta: dict[str, Any] = field(default_factory=dict)


def plan_self_healing(*, cognition_intent: str, confidence: float, capabilities: list[str]) -> SelfHealingPlan:
    if cognition_intent == "create_fix_plan" and confidence >= 0.8:
        return SelfHealingPlan(
            ok=True,
            stage="propose_repair",
            summary="Evidence supports a governed fix plan proposal.",
            proposed_capabilities=capabilities,
            requires_approval=True,
            confidence=confidence,
        )
    if cognition_intent == "diagnose_failure":
        return SelfHealingPlan(
            ok=True,
            stage="investigate",
            summary="Collect evidence before proposing mutation.",
            proposed_capabilities=capabilities,
            requires_approval=True,
            confidence=confidence,
            evidence_gaps=["Confirm root cause before restart/redeploy"],
        )
    return SelfHealingPlan(
        ok=False,
        stage="detect",
        summary="Insufficient confidence for self-healing action.",
        proposed_capabilities=[],
        requires_approval=True,
        confidence=confidence,
    )

# SPDX-License-Identifier: Apache-2.0
"""Mutation escalation — dynamic mutation tier elevation."""

from __future__ import annotations

from typing import Any


_TIER_ORDER = ("E1_proposal_only", "E2_branch_diff", "E3_pr_creation")


def assess_mutation_escalation(
    *,
    pressure: dict[str, Any],
    validation_successes: int = 0,
    base_tier: str = "E2_branch_diff",
) -> dict[str, Any]:
    """Elevate mutation tier based on operational pressure — never auto-execute."""
    tier = base_tier
    escalated = False
    reason = "Baseline tier — no escalation triggers."

    if pressure.get("elevated") and int(pressure.get("restart_count") or 0) >= 3:
        tier = "E3_pr_creation"
        escalated = True
        reason = "Repeated deployment failures — E2 elevated to E3 (deeper approval required)."
    elif pressure.get("elevated") and int(pressure.get("workflow_failure_count") or 0) >= 3:
        tier = "E3_pr_creation"
        escalated = True
        reason = "Repeated workflow failures — mutation tier elevated to E3."

    if validation_successes >= 100 and not escalated:
        tier = "E2_branch_diff" if tier == "E3_pr_creation" else tier
        reason = f"Stability reward: {validation_successes} successful validations — review friction reduced."

    cooldown_active = int(pressure.get("restart_count") or 0) >= 3 and pressure.get("elevated")
    restricted_mutations: list[str] = []
    if cooldown_active:
        restricted_mutations = ["restart", "deploy_retry"]

    return {
        "current_tier": tier,
        "base_tier": base_tier,
        "escalated": escalated,
        "escalation_reason": reason,
        "cooldown_active": cooldown_active,
        "restricted_mutations": restricted_mutations,
        "approval_required": True,
        "autonomous_execution_blocked": True,
    }

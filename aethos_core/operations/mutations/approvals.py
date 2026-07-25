# SPDX-License-Identifier: Apache-2.0
"""Mutation approval model — escalated tiers (design)."""

from __future__ import annotations

from aethos_core.operations.mutations.risk import MutationRiskTier, execution_allowed_for_tier


def approval_required_for_tier(tier: MutationRiskTier) -> bool:
    return tier not in (MutationRiskTier.T0_READONLY,)


def can_approve_mutation(*, tier: MutationRiskTier, execution_approved: bool = False) -> bool:
    if execution_approved:
        return False
    if tier == MutationRiskTier.T5_BLOCKED:
        return False
    return approval_required_for_tier(tier) and not execution_allowed_for_tier(tier)

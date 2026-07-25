# SPDX-License-Identifier: Apache-2.0
"""Mutation risk tiers — T0 readonly through T5 blocked."""

from __future__ import annotations

from enum import Enum
from typing import Any


class MutationRiskTier(str, Enum):
    T0_READONLY = "T0_readonly"
    T1_DRY_RUN = "T1_dry_run"
    T2_LOW_RISK = "T2_low_risk_mutation"
    T3_PRODUCTION = "T3_production_impacting"
    T4_IRREVERSIBLE = "T4_irreversible"
    T5_BLOCKED = "T5_blocked"


def enabled_execution_tiers() -> frozenset[MutationRiskTier]:
    from aethos_core.config import get_settings

    settings = get_settings()
    tiers: set[MutationRiskTier] = {MutationRiskTier.T1_DRY_RUN}
    if settings.mutation_execution_enabled:
        tiers.add(MutationRiskTier.T2_LOW_RISK)
    if settings.mutation_t3_production_enabled:
        tiers.add(MutationRiskTier.T3_PRODUCTION)
    return frozenset(tiers)


EXECUTION_ENABLED_TIERS = enabled_execution_tiers()


def classify_mutation_risk(
    *,
    operation_type: str,
    provider: str,
    target_status: str = "unknown",
    production_impact: bool | None = None,
) -> MutationRiskTier:
    if operation_type in ("local_commit_preflight", "local_push_preflight", "git_deploy_preflight"):
        return MutationRiskTier.T4_IRREVERSIBLE
    if operation_type == "social_post":
        return MutationRiskTier.T3_PRODUCTION
    if operation_type in ("create_branch", "create_pr", "workflow_rerun"):
        return MutationRiskTier.T2_LOW_RISK
    if operation_type in ("redeploy", "restart", "set_env_var", "deploy_from_git"):
        if production_impact is True or target_status == "resolved":
            return MutationRiskTier.T3_PRODUCTION
        return MutationRiskTier.T2_LOW_RISK
    if provider == "unknown":
        return MutationRiskTier.T5_BLOCKED
    return MutationRiskTier.T3_PRODUCTION


def tier_label(tier: MutationRiskTier) -> str:
    return tier.value.replace("_", " ")


def execution_allowed_for_tier(tier: MutationRiskTier) -> bool:
    return tier in enabled_execution_tiers()


def tier_to_dict(tier: MutationRiskTier) -> dict[str, Any]:
    return {
        "tier": tier.value,
        "label": tier_label(tier),
        "execution_enabled": execution_allowed_for_tier(tier),
    }

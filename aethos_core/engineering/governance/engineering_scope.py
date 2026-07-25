# SPDX-License-Identifier: Apache-2.0
"""Engineering risk tiers E0–E5 and scope validation."""

from __future__ import annotations

from enum import Enum
from typing import Any

from aethos_core.local_workspace.mutations.foundation import BLOCKED_AUTONOMOUS_ACTIONS


class EngineeringRiskTier(str, Enum):
    E0_READONLY = "E0_readonly"
    E1_PROPOSAL = "E1_proposal_only"
    E2_BRANCH_DIFF = "E2_branch_diff"
    E3_PR_CREATION = "E3_pr_creation"
    E4_PRODUCTION = "E4_production_impacting"
    E5_BLOCKED = "E5_blocked"


EXECUTION_ALLOWED_TIERS = frozenset({EngineeringRiskTier.E2_BRANCH_DIFF, EngineeringRiskTier.E3_PR_CREATION})


def classify_engineering_risk(
    *,
    operation: str,
    files_count: int = 0,
    touches_governance: bool = False,
    touches_credentials: bool = False,
    production_impact: bool = False,
) -> EngineeringRiskTier:
    if operation in BLOCKED_AUTONOMOUS_ACTIONS or touches_credentials:
        return EngineeringRiskTier.E5_BLOCKED
    if touches_governance and not production_impact:
        return EngineeringRiskTier.E4_PRODUCTION
    if operation in ("engineering_preflight", "patch_plan", "task_intake"):
        return EngineeringRiskTier.E1_PROPOSAL
    if operation in ("engineering_execution", "create_branch", "generate_patch"):
        if production_impact or files_count > 20:
            return EngineeringRiskTier.E4_PRODUCTION
        return EngineeringRiskTier.E2_BRANCH_DIFF
    if operation in ("create_pr", "pr_generation"):
        return EngineeringRiskTier.E3_PR_CREATION
    if operation in ("validation", "verification"):
        return EngineeringRiskTier.E0_READONLY
    return EngineeringRiskTier.E1_PROPOSAL


def validate_scope(
    *,
    allowed_files: list[str],
    requested_files: list[str],
    max_files: int = 12,
    max_diff_bytes: int = 120_000,
) -> dict[str, Any]:
    blocked = [f for f in requested_files if f.startswith(".github/workflows/") and "delete" in f.lower()]
    over_limit = len(requested_files) > max_files
    out_of_scope = [f for f in requested_files if allowed_files and f not in allowed_files]
    ok = not over_limit and not blocked and not out_of_scope
    return {
        "ok": ok,
        "files_requested": requested_files,
        "files_allowed": allowed_files,
        "out_of_scope": out_of_scope,
        "blocked_paths": blocked,
        "max_files": max_files,
        "max_diff_bytes": max_diff_bytes,
        "scope_valid": ok,
    }


def tier_label(tier: EngineeringRiskTier) -> str:
    return tier.value.replace("_", " ")


def execution_allowed(tier: EngineeringRiskTier) -> bool:
    return tier in EXECUTION_ALLOWED_TIERS

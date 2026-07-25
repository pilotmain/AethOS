# SPDX-License-Identifier: Apache-2.0
"""FIX 125A — issue → plan software delivery contract."""

from __future__ import annotations

from typing import Final, Literal

IssuePlanStatus = Literal[
    "intake",
    "analyzed",
    "plan_drafted",
    "planning_approved",
    "blocked",
]

ISSUE_PLAN_SCHEMA_VERSION: Final[str] = "software_delivery_issue_plan_v1"
ISSUE_PLAN_FIX: Final[str] = "FIX 125A"

PLANNING_APPROVAL_PHRASE: Final[str] = (
    "I approve this governed software delivery implementation plan for human review."
)

AUTONOMOUS_MERGE_PERMITTED: Final[bool] = False
INFRA_MUTATION_PERMITTED: Final[bool] = False
CODE_GENERATION_ENABLED_FIX_125A: Final[bool] = False
AUTO_SCOPE_EXPANSION_PERMITTED: Final[bool] = False

SOFTWARE_DELIVERY_LANE_ID: Final[str] = "software_delivery_issue_plan"
INFRA_ORCHESTRATION_LANE_ID: Final[str] = "infrastructure_orchestration"

BLOCKED_ACTIONS_FIX_125A: Final[tuple[str, ...]] = (
    "auto_merge_to_main",
    "deploy_to_production",
    "mutate_railway_infra",
    "bypass_approvals",
    "rewrite_unrelated_systems",
    "self_expand_scope",
    "autonomous_code_generation",
)

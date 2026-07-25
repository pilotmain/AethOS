# SPDX-License-Identifier: Apache-2.0
"""FIX 127 — bounded multi-agent role contract (advisory only)."""

from __future__ import annotations

from typing import Final

MULTI_AGENT_SCHEMA_VERSION: Final[str] = "software_delivery_multi_agent_v1"
MULTI_AGENT_FIX: Final[str] = "FIX 127"

# Advisory collaboration only — no ExecutorAgent in FIX 127.
BOUNDED_AGENT_ROLE_IDS: Final[tuple[str, ...]] = (
    "planner_agent",
    "reviewer_agent",
    "verification_agent",
    "risk_agent",
    "diff_audit_agent",
)

AGENT_ALLOWED_SCOPES: Final[tuple[str, ...]] = (
    "planning",
    "analysis",
    "verification",
    "review",
    "risk_assessment",
    "patch_proposal_review",
)

AGENT_FORBIDDEN_SCOPES: Final[tuple[str, ...]] = (
    "merge",
    "deploy",
    "railway_mutation",
    "infra_mutation",
    "bypass_approval",
    "rollout_promotion",
    "autonomous_execution",
    "workspace_write",
    "github_mutation",
)

EXECUTOR_AGENT_ENABLED_FIX_127: Final[bool] = False
MUTATION_PERFORMED_FIX_127: Final[bool] = False
SELF_AUTHORIZING_FIX_127: Final[bool] = False

MULTI_AGENT_RECEIPT_PHASES: Final[tuple[str, ...]] = (
    "collaboration_started",
    "agent_role_completed",
    "collaboration_completed",
)

# SPDX-License-Identifier: Apache-2.0
"""FIX 149 — multi-operator governance collaboration contract."""

from __future__ import annotations

from typing import Final

GOVERNANCE_COLLABORATION_SCHEMA_VERSION: Final[str] = "mission_control_governance_collaboration_v1"
GOVERNANCE_COLLABORATION_RECORD_SCHEMA_VERSION: Final[str] = "mission_control_governance_collaboration_record_v1"
GOVERNANCE_COLLABORATION_FIX: Final[str] = "FIX 149"

MUTATION_PERFORMED_FIX_149: Final[bool] = False
DELEGATED_EXECUTION_AUTHORITY_ENABLED_FIX_149: Final[bool] = False
AUTOMATIC_QUORUM_APPROVAL_ENABLED_FIX_149: Final[bool] = False
AUTOMATIC_MERGE_DEPLOY_ENABLED_FIX_149: Final[bool] = False
AUTONOMOUS_ORGANIZATIONAL_DECISIONS_ENABLED_FIX_149: Final[bool] = False
GOVERNANCE_MUTATION_PERFORMED_FIX_149: Final[bool] = False

GOVERNANCE_COLLABORATION_ROUTE_ID: Final[str] = "mission_control_governance_collaboration"

GOVERNANCE_COLLABORATION_INVARIANT: Final[str] = (
    "governance_collaboration_is_multi_operator_institutional_continuity_no_delegated_execution_authority"
)

COLLABORATION_RECORD_KINDS: Final[tuple[str, ...]] = (
    "named_reviewer",
    "reviewer_assignment",
    "reviewer_acknowledgment",
    "review_ownership",
    "delegated_review_request",
    "governance_handoff",
    "unresolved_concern_escalation",
    "role_deliberation",
    "quorum_discussion",
)

REVIEWER_ROLES: Final[tuple[str, ...]] = (
    "primary_reviewer",
    "secondary_reviewer",
    "observer",
    "escalation_owner",
    "mission_owner",
)

DEFAULT_QUORUM_ADVISORY_SIZE: Final[int] = 2

MAX_COLLABORATION_CONTENT_LEN: Final[int] = 4000
MAX_PERSISTED_COLLABORATION_RECORDS: Final[int] = 500

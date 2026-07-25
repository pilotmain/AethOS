# SPDX-License-Identifier: Apache-2.0
"""FIX 150 — governance role architecture contract."""

from __future__ import annotations

from typing import Final

GOVERNANCE_ROLE_ARCHITECTURE_SCHEMA_VERSION: Final[str] = "mission_control_governance_role_architecture_v1"
GOVERNANCE_ROLE_ARCHITECTURE_FIX: Final[str] = "FIX 150"

MUTATION_PERFORMED_FIX_150: Final[bool] = False
DELEGATED_EXECUTION_AUTHORITY_ENABLED_FIX_150: Final[bool] = False
AUTOMATIC_APPROVAL_ENABLED_FIX_150: Final[bool] = False
AUTONOMOUS_ROLE_ELEVATION_ENABLED_FIX_150: Final[bool] = False
AUTOMATIC_POLICY_MUTATION_ENABLED_FIX_150: Final[bool] = False
GOVERNANCE_MUTATION_PERFORMED_FIX_150: Final[bool] = False

GOVERNANCE_ROLE_ARCHITECTURE_ROUTE_ID: Final[str] = "mission_control_governance_role_architecture"

GOVERNANCE_ROLE_ARCHITECTURE_INVARIANT: Final[str] = (
    "governance_role_architecture_is_read_only_institutional_topology_no_delegated_execution_or_role_elevation"
)

GOVERNANCE_ROLE_TAXONOMY: Final[tuple[str, ...]] = (
    "primary_reviewer",
    "secondary_reviewer",
    "observer",
    "escalation_owner",
    "mission_owner",
    "deliberation_author",
    "approval_operator",
    "execution_operator",
)

TRUST_ZONES: Final[tuple[str, ...]] = (
    "observability",
    "deliberation_memory",
    "collaboration_memory",
    "readiness_advisory",
    "chat_governed_approval",
    "execution_substrate",
)

ESCALATION_PATHS: Final[tuple[tuple[str, str], ...]] = (
    ("observer", "primary_reviewer"),
    ("primary_reviewer", "secondary_reviewer"),
    ("secondary_reviewer", "escalation_owner"),
    ("escalation_owner", "mission_owner"),
)

SEPARATION_OF_DUTY_POLICIES: Final[tuple[str, ...]] = (
    "primary_reviewer_cannot_auto_approve_without_chat_governance",
    "deliberation_memory_does_not_grant_execution_authority",
    "collaboration_acknowledgment_does_not_equal_quorum_approval",
    "readiness_advisory_go_no_go_is_not_executable",
    "execution_substrate_requires_explicit_human_approval_phrases",
)

QUORUM_ROLE_COMPOSITION: Final[tuple[str, ...]] = (
    "primary_reviewer",
    "secondary_reviewer",
)

DEFAULT_ADVISORY_QUORUM_SIZE: Final[int] = 2

# SPDX-License-Identifier: Apache-2.0
"""FIX 148 — governance deliberation workspace contract."""

from __future__ import annotations

from typing import Final

GOVERNANCE_DELIBERATION_SCHEMA_VERSION: Final[str] = "mission_control_governance_deliberation_v1"
GOVERNANCE_DELIBERATION_RECORD_SCHEMA_VERSION: Final[str] = "mission_control_governance_deliberation_record_v1"
GOVERNANCE_DELIBERATION_FIX: Final[str] = "FIX 148"

MUTATION_PERFORMED_FIX_148: Final[bool] = False
GOVERNANCE_MUTATION_PERFORMED_FIX_148: Final[bool] = False
AUTOMATIC_APPROVAL_ENABLED_FIX_148: Final[bool] = False
AUTOMATIC_REJECTION_ENABLED_FIX_148: Final[bool] = False
AUTONOMOUS_POLICY_EVOLUTION_ENABLED_FIX_148: Final[bool] = False
DELEGATED_AUTHORITY_ENABLED_FIX_148: Final[bool] = False

GOVERNANCE_DELIBERATION_ROUTE_ID: Final[str] = "mission_control_governance_deliberation"

GOVERNANCE_DELIBERATION_INVARIANT: Final[str] = (
    "governance_deliberation_is_collaborative_reasoning_memory_no_approval_automation_or_policy_mutation"
)

DELIBERATION_RECORD_KINDS: Final[tuple[str, ...]] = (
    "operator_note",
    "reviewer_annotation",
    "structured_concern",
    "dissent",
    "rationale",
    "alternative_path",
    "checklist_item",
    "approval_rejection_rationale",
    "decision_justification",
)

DEFAULT_REVIEW_CHECKLIST: Final[tuple[str, ...]] = (
    "readiness_score_reviewed",
    "blockers_addressed_or_accepted",
    "pending_approvals_reviewed",
    "evidence_gaps_acknowledged",
    "rollback_posture_understood",
    "incident_exposure_assessed",
    "go_no_go_hold_discussed",
    "human_authority_confirmed",
)

MAX_DELIBERATION_CONTENT_LEN: Final[int] = 4000
MAX_PERSISTED_DELIBERATION_RECORDS: Final[int] = 500

# SPDX-License-Identifier: Apache-2.0
"""FIX 166 — human decision board + action selection contract."""

from __future__ import annotations

from typing import Final

HUMAN_DECISION_BOARD_SCHEMA_VERSION: Final[str] = "mission_control_human_decision_board_v1"
HUMAN_DECISION_BOARD_RECORD_SCHEMA_VERSION: Final[str] = "mission_control_human_decision_board_record_v1"
HUMAN_DECISION_BOARD_FIX: Final[str] = "FIX 166"

MUTATION_PERFORMED_FIX_166: Final[bool] = False
AUTOMATIC_POLICY_MUTATION_ENABLED_FIX_166: Final[bool] = False
AUTONOMOUS_SELECTION_ENABLED_FIX_166: Final[bool] = False
AUTONOMOUS_EXECUTION_ENABLED_FIX_166: Final[bool] = False
AUTONOMOUS_APPROVAL_ENABLED_FIX_166: Final[bool] = False
AUTONOMOUS_PR_CREATION_ENABLED_FIX_166: Final[bool] = False
AUTONOMOUS_MERGE_ENABLED_FIX_166: Final[bool] = False
AUTONOMOUS_RAILWAY_MUTATION_ENABLED_FIX_166: Final[bool] = False
GOVERNANCE_MUTATION_PERFORMED_FIX_166: Final[bool] = False

HUMAN_DECISION_BOARD_ROUTE_ID: Final[str] = "mission_control_human_decision_board"

HUMAN_DECISION_BOARD_INVARIANT: Final[str] = (
    "human_decision_board_records_human_choice_only_no_autonomous_selection_or_execution_authority"
)

DECISION_RECORD_KINDS: Final[tuple[str, ...]] = (
    "selection_record",
    "rejection_note",
    "rationale_note",
    "tradeoff_acceptance_note",
    "risk_acceptance_note",
    "decision_artifact",
    "approval_artifact",
    "execution_handoff_artifact",
)

DECISION_PRINCIPLES: Final[tuple[tuple[str, str], ...]] = (
    ("humans_select_not_system", "Only humans select institutional paths; AethOS never auto-selects."),
    ("selection_recorded_not_inferred", "Human selection is explicitly recorded; never inferred autonomously."),
    ("rejections_visible", "Rejected paths are captured alongside the selected path."),
    ("rationale_required_for_traceability", "Decision rationale is a first-class institutional artifact."),
    ("tradeoffs_consciously_accepted", "Known tradeoffs accepted are recorded at decision time."),
    ("risks_consciously_accepted", "Known risks accepted are recorded at decision time."),
    ("traceability_complete", "Who, when, evidence, and agent participation are traceable."),
    ("handoff_advisory_not_executed", "Execution handoff artifacts assist lane entry; never execute autonomously."),
)

DECISION_BOARD_EXECUTABLE: Final[bool] = False

MAX_DECISION_CONTENT_LEN: Final[int] = 4000
MAX_PERSISTED_DECISION_RECORDS: Final[int] = 500

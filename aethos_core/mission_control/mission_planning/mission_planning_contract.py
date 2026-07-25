# SPDX-License-Identifier: Apache-2.0
"""FIX 164 — mission planning + institutional action cognition contract."""

from __future__ import annotations

from typing import Final

MISSION_PLANNING_SCHEMA_VERSION: Final[str] = "mission_control_mission_planning_v1"
MISSION_PLANNING_RECORD_SCHEMA_VERSION: Final[str] = "mission_control_mission_planning_record_v1"
MISSION_PLANNING_FIX: Final[str] = "FIX 164"

MUTATION_PERFORMED_FIX_164: Final[bool] = False
AUTOMATIC_POLICY_MUTATION_ENABLED_FIX_164: Final[bool] = False
AUTONOMOUS_ACTION_EXECUTION_ENABLED_FIX_164: Final[bool] = False
AUTONOMOUS_APPROVAL_ENABLED_FIX_164: Final[bool] = False
AUTO_PATH_SELECTION_ENABLED_FIX_164: Final[bool] = False
RAILWAY_MUTATION_ENABLED_FIX_164: Final[bool] = False
PR_OPEN_ENABLED_FIX_164: Final[bool] = False
MERGE_DEPLOY_RESTART_ENABLED_FIX_164: Final[bool] = False
GOVERNANCE_MUTATION_PERFORMED_FIX_164: Final[bool] = False

MISSION_PLANNING_ROUTE_ID: Final[str] = "mission_control_mission_planning"

MISSION_PLANNING_INVARIANT: Final[str] = (
    "mission_planning_is_institutional_action_cognition_recommendation_only_no_execution_authority_or_autonomous_path_selection"
)

PLANNING_RECORD_KINDS: Final[tuple[str, ...]] = (
    "action_option_note",
    "option_comparison_note",
    "lane_mapping_note",
    "required_approval_note",
    "constitutional_tradeoff_note",
    "risk_blocker_note",
    "do_not_do_path_note",
    "review_sequence_note",
    "mission_action_plan_artifact",
)

PLANNING_PRINCIPLES: Final[tuple[tuple[str, str], ...]] = (
    ("options_generated_not_executed", "Institutional action options are generated; execution remains human-governed."),
    ("comparison_assists_not_selects", "Option comparison assists deliberation; no autonomous path selection."),
    ("lanes_mapped_not_mutated", "Lane touch mapping is advisory; planning never mutates lanes."),
    ("approvals_listed_not_granted", "Required approvals are listed; planning never approves actions."),
    ("tradeoffs_surfaced_not_decided", "Constitutional tradeoffs from synthesis inform planning; humans decide."),
    ("risks_visible_not_bypassed", "Risks and blockers are surfaced; planning does not bypass governance."),
    ("do_not_do_paths_explicit", "Do-not-do paths are identified to prevent unsafe institutional action."),
    ("review_sequence_advisory", "Operator review sequence is recommended; humans govern final order."),
    ("planning_cognition_not_authority", "Mission action plan artifacts assist reasoning; never grant execution authority."),
)

ACTION_OPTION_CATALOG: Final[tuple[tuple[str, str, str, tuple[str, ...]], ...]] = (
    (
        "constitutional_review_path",
        "Constitutional review + human approval",
        "Review constitutional synthesis and tradeoffs before any lane execution.",
        ("software_delivery", "route_diagnostics"),
    ),
    (
        "evidence_gathering_path",
        "Cross-lane evidence gathering",
        "Collect observability, replay, and readiness evidence without lane mutation.",
        ("route_diagnostics", "durable_jobs"),
    ),
    (
        "governed_delivery_continuation",
        "Governed software delivery continuation",
        "Continue software delivery loop with explicit human approval at each gate.",
        ("software_delivery", "multi_agent_collaboration"),
    ),
    (
        "hold_no_go_path",
        "Hold / institutional pause",
        "Pause institutional action until blockers, approvals, and constitutional tensions are resolved.",
        (),
    ),
)

DO_NOT_DO_CATALOG: Final[tuple[tuple[str, str], ...]] = (
    ("autonomous_execution", "Do not execute actions autonomously from planning cognition."),
    ("autonomous_approval", "Do not approve actions or gates from planning cognition."),
    ("auto_path_selection", "Do not auto-select a final institutional path."),
    ("railway_mutation", "Do not mutate Railway infrastructure from planning cognition."),
    ("pr_open_merge_deploy", "Do not open PRs, merge, deploy, or restart from planning cognition."),
    ("bypass_constitutional_tradeoffs", "Do not bypass constitutional tradeoffs surfaced by synthesis."),
)

PLANNING_RECOMMENDATION_EXECUTABLE: Final[bool] = False

MAX_PLANNING_CONTENT_LEN: Final[int] = 4000
MAX_PERSISTED_PLANNING_RECORDS: Final[int] = 500

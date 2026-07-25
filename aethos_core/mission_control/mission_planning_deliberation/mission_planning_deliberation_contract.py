# SPDX-License-Identifier: Apache-2.0
"""FIX 165 — mission planning multi-agent deliberation contract."""

from __future__ import annotations

from typing import Final

MISSION_PLANNING_DELIBERATION_SCHEMA_VERSION: Final[str] = "mission_control_mission_planning_deliberation_v1"
MISSION_PLANNING_DELIBERATION_RECORD_SCHEMA_VERSION: Final[str] = (
    "mission_control_mission_planning_deliberation_record_v1"
)
MISSION_PLANNING_DELIBERATION_FIX: Final[str] = "FIX 165"

MUTATION_PERFORMED_FIX_165: Final[bool] = False
AUTOMATIC_POLICY_MUTATION_ENABLED_FIX_165: Final[bool] = False
AUTONOMOUS_EXECUTION_ENABLED_FIX_165: Final[bool] = False
AUTONOMOUS_APPROVAL_ENABLED_FIX_165: Final[bool] = False
AUTONOMOUS_LANE_SELECTION_ENABLED_FIX_165: Final[bool] = False
AUTONOMOUS_PR_CREATION_ENABLED_FIX_165: Final[bool] = False
AUTONOMOUS_RAILWAY_MUTATION_ENABLED_FIX_165: Final[bool] = False
AUTONOMOUS_MERGE_ENABLED_FIX_165: Final[bool] = False
GOVERNANCE_MUTATION_PERFORMED_FIX_165: Final[bool] = False

MISSION_PLANNING_DELIBERATION_ROUTE_ID: Final[str] = "mission_control_mission_planning_deliberation"

MISSION_PLANNING_DELIBERATION_INVARIANT: Final[str] = (
    "mission_planning_deliberation_is_bounded_multi_agent_analysis_only_no_execution_authority_or_autonomous_selection"
)

BOUNDED_DELIBERATION_AGENT_ROLE_IDS: Final[tuple[str, ...]] = (
    "planner_agent",
    "risk_agent",
    "constitutional_agent",
    "delivery_agent",
    "verification_agent",
    "synthesis_agent",
)

DELIBERATION_AGENT_CATALOG: Final[tuple[tuple[str, str, str], ...]] = (
    ("planner_agent", "PlannerAgent", "What institutional paths exist?"),
    ("risk_agent", "RiskAgent", "What can go wrong?"),
    ("constitutional_agent", "ConstitutionalAgent", "What constitutional tensions exist?"),
    ("delivery_agent", "DeliveryAgent", "What execution lanes would be touched?"),
    ("verification_agent", "VerificationAgent", "What evidence is missing?"),
    ("synthesis_agent", "SynthesisAgent", "Summarize multi-agent findings for human review."),
)

DELIBERATION_RECORD_KINDS: Final[tuple[str, ...]] = (
    "planner_analysis_note",
    "risk_analysis_note",
    "constitutional_analysis_note",
    "delivery_analysis_note",
    "verification_analysis_note",
    "synthesis_summary_note",
    "deliberation_record",
)

DELIBERATION_PRINCIPLES: Final[tuple[tuple[str, str], ...]] = (
    ("agents_analyze_not_execute", "Bounded agents produce analysis only; no autonomous execution."),
    ("agents_advise_not_approve", "Agents surface required approvals; never grant them."),
    ("agents_map_not_mutate_lanes", "DeliveryAgent maps lane touches; agents never mutate lanes."),
    ("constitutional_agent_bounded", "ConstitutionalAgent surfaces tensions; never arbitrates constitutionally."),
    ("verification_agent_readonly", "VerificationAgent identifies evidence gaps; never runs mutations."),
    ("synthesis_agent_consolidates_not_selects", "SynthesisAgent summarizes findings; humans select path."),
    ("no_autonomous_lane_selection", "Multi-agent deliberation never auto-selects institutional path."),
    ("no_executor_agent", "No ExecutorAgent — deliberation remains analysis-only."),
)

DELIBERATION_RECOMMENDATION_EXECUTABLE: Final[bool] = False

MAX_DELIBERATION_CONTENT_LEN: Final[int] = 4000
MAX_PERSISTED_DELIBERATION_RECORDS: Final[int] = 500

# SPDX-License-Identifier: Apache-2.0
"""FIX 169 — work package readiness + lane admission contract."""

from __future__ import annotations

from typing import Final

WORK_PACKAGE_READINESS_LANE_ADMISSION_SCHEMA_VERSION: Final[str] = (
    "mission_control_work_package_readiness_lane_admission_v1"
)
WORK_PACKAGE_READINESS_LANE_ADMISSION_RECORD_SCHEMA_VERSION: Final[str] = (
    "mission_control_work_package_readiness_lane_admission_record_v1"
)
WORK_PACKAGE_READINESS_LANE_ADMISSION_FIX: Final[str] = "FIX 169"

MUTATION_PERFORMED_FIX_169: Final[bool] = False
AUTOMATIC_POLICY_MUTATION_ENABLED_FIX_169: Final[bool] = False
AUTONOMOUS_EXECUTION_ENABLED_FIX_169: Final[bool] = False
AUTONOMOUS_APPROVAL_ENABLED_FIX_169: Final[bool] = False
AUTONOMOUS_LANE_ENTRY_ENABLED_FIX_169: Final[bool] = False
CODE_WRITE_ENABLED_FIX_169: Final[bool] = False
PR_ACTION_ENABLED_FIX_169: Final[bool] = False
MERGE_DEPLOY_ENABLED_FIX_169: Final[bool] = False
RAILWAY_MUTATION_ENABLED_FIX_169: Final[bool] = False
GOVERNANCE_MUTATION_PERFORMED_FIX_169: Final[bool] = False

WORK_PACKAGE_READINESS_LANE_ADMISSION_ROUTE_ID: Final[str] = (
    "mission_control_work_package_readiness_lane_admission"
)

WORK_PACKAGE_READINESS_LANE_ADMISSION_INVARIANT: Final[str] = (
    "work_package_readiness_evaluates_lane_admission_eligibility_recommendation_only_no_execution_authority"
)

PACKAGE_LANE_MAP: Final[tuple[tuple[str, tuple[str, ...]], ...]] = (
    ("planner_agent", ("software_delivery",)),
    ("risk_agent", ("software_delivery", "route_diagnostics")),
    ("verification_agent", ("software_delivery",)),
    ("delivery_agent", ("software_delivery", "multi_agent_collaboration")),
    ("diff_audit_agent", ("software_delivery",)),
)

PACKAGE_PREREQUISITES: Final[tuple[tuple[str, tuple[str, ...]], ...]] = (
    ("risk_agent", ("planner_agent",)),
    ("verification_agent", ("planner_agent",)),
    ("delivery_agent", ("planner_agent", "risk_agent")),
    ("diff_audit_agent", ("planner_agent",)),
)

LANE_ADMISSION_RECORD_KINDS: Final[tuple[str, ...]] = (
    "lane_admission_artifact",
    "readiness_check_note",
    "admission_blocker_note",
    "lane_mapping_note",
    "prerequisite_note",
    "admission_forbidden_note",
    "lane_admission_record",
)

LANE_ADMISSION_PRINCIPLES: Final[tuple[tuple[str, str], ...]] = (
    ("work_packages_required", "Readiness evaluation requires FIX 168 work package context."),
    ("readiness_evaluates_not_executes", "Readiness checks eligibility; never executes lane entry."),
    ("admission_maps_not_enters", "Lane admission maps packages to lanes; never enters autonomously."),
    ("approvals_checked_not_granted", "Required approvals are checked; readiness never grants them."),
    ("gates_checked_not_passed", "Required gates are checked; readiness never passes them autonomously."),
    ("blockers_surfaced_not_bypassed", "Admission blockers are surfaced; readiness does not bypass governance."),
    ("artifact_prepared_not_executed", "Lane admission artifact prepares future execution; never auto-runs."),
    ("humans_authorize_entry", "Humans authorize lane entry — readiness determines eligibility only."),
)

FORBIDDEN_ADMISSION_ACTIONS: Final[tuple[tuple[str, str], ...]] = (
    ("autonomous_lane_entry", "Readiness never enters governed lanes autonomously."),
    ("code_write", "Readiness never writes code or mutates workspace."),
    ("pr_open", "Readiness never opens or mutates PRs."),
    ("merge_deploy", "Readiness never merges or deploys."),
    ("railway_mutation", "Readiness never mutates Railway infrastructure."),
    ("autonomous_execution", "Readiness never executes delivery lane actions."),
    ("autonomous_approval", "Readiness never approves gates or inbox items."),
)

LANE_ADMISSION_RECOMMENDATION_EXECUTABLE: Final[bool] = False

MAX_LANE_ADMISSION_CONTENT_LEN: Final[int] = 4000
MAX_PERSISTED_LANE_ADMISSION_RECORDS: Final[int] = 500

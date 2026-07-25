# SPDX-License-Identifier: Apache-2.0
"""FIX 168 — bounded multi-agent delivery work packages contract."""

from __future__ import annotations

from typing import Final

BOUNDED_DELIVERY_WORK_PACKAGES_SCHEMA_VERSION: Final[str] = (
    "mission_control_bounded_delivery_work_packages_v1"
)
BOUNDED_DELIVERY_WORK_PACKAGES_RECORD_SCHEMA_VERSION: Final[str] = (
    "mission_control_bounded_delivery_work_packages_record_v1"
)
BOUNDED_DELIVERY_WORK_PACKAGES_FIX: Final[str] = "FIX 168"

MUTATION_PERFORMED_FIX_168: Final[bool] = False
AUTOMATIC_POLICY_MUTATION_ENABLED_FIX_168: Final[bool] = False
AUTONOMOUS_EXECUTION_ENABLED_FIX_168: Final[bool] = False
AUTONOMOUS_APPROVAL_ENABLED_FIX_168: Final[bool] = False
CODE_WRITE_ENABLED_FIX_168: Final[bool] = False
PR_ACTION_ENABLED_FIX_168: Final[bool] = False
MERGE_DEPLOY_ENABLED_FIX_168: Final[bool] = False
RAILWAY_MUTATION_ENABLED_FIX_168: Final[bool] = False
GOVERNANCE_MUTATION_PERFORMED_FIX_168: Final[bool] = False

BOUNDED_DELIVERY_WORK_PACKAGES_ROUTE_ID: Final[str] = (
    "mission_control_bounded_multi_agent_delivery_work_packages"
)

BOUNDED_DELIVERY_WORK_PACKAGES_INVARIANT: Final[str] = (
    "bounded_delivery_work_packages_convert_handoff_to_role_scoped_packages_recommendation_only_no_execution_authority"
)

BOUNDED_DELIVERY_AGENT_ROLE_IDS: Final[tuple[str, ...]] = (
    "planner_agent",
    "risk_agent",
    "verification_agent",
    "delivery_agent",
    "diff_audit_agent",
)

DELIVERY_AGENT_CATALOG: Final[tuple[tuple[str, str, str], ...]] = (
    ("planner_agent", "PlannerAgent", "Scope delivery stages and work sequencing"),
    ("risk_agent", "RiskAgent", "Assess delivery risk and blast radius"),
    ("verification_agent", "VerificationAgent", "Define verification inputs and evidence gaps"),
    ("delivery_agent", "DeliveryAgent", "Map governed lane touches without execution"),
    ("diff_audit_agent", "DiffAuditAgent", "Audit patch proposals and diff scope"),
)

WORK_PACKAGES_RECORD_KINDS: Final[tuple[str, ...]] = (
    "work_package_artifact",
    "planner_package_note",
    "risk_package_note",
    "verification_package_note",
    "delivery_package_note",
    "diff_audit_package_note",
    "package_gate_note",
    "package_forbidden_note",
    "delivery_work_packages_record",
)

WORK_PACKAGES_PRINCIPLES: Final[tuple[tuple[str, str], ...]] = (
    ("handoff_required", "Work packages require FIX 167 handoff artifact context."),
    ("packages_scope_not_execute", "Packages scope bounded agent work; never execute delivery."),
    ("agents_assigned_not_authorized", "Agents are assigned packages; never granted execution authority."),
    ("inputs_outputs_defined_not_mutated", "Inputs and outputs are defined; no code writes or PR actions."),
    ("gates_listed_not_passed", "Required gates are listed; packages never pass gates autonomously."),
    ("forbidden_actions_explicit", "Forbidden actions remain explicit at package boundary."),
    ("artifacts_persisted_not_executed", "Package artifacts persist for human review; never auto-run."),
    ("no_executor_agent", "No ExecutorAgent — packages prepare bounded delivery only."),
)

FORBIDDEN_PACKAGE_ACTIONS: Final[tuple[tuple[str, str], ...]] = (
    ("code_write", "Work packages never write code or mutate workspace."),
    ("pr_open", "Work packages never open or mutate PRs."),
    ("merge_deploy", "Work packages never merge or deploy."),
    ("railway_mutation", "Work packages never mutate Railway infrastructure."),
    ("autonomous_execution", "Work packages never execute delivery lane actions."),
    ("autonomous_approval", "Work packages never approve gates or inbox items."),
)

WORK_PACKAGES_RECOMMENDATION_EXECUTABLE: Final[bool] = False

MAX_WORK_PACKAGES_CONTENT_LEN: Final[int] = 4000
MAX_PERSISTED_WORK_PACKAGES_RECORDS: Final[int] = 500

# SPDX-License-Identifier: Apache-2.0
"""FIX 189 — bounded multi-agent delivery execution contract."""

from __future__ import annotations

from typing import Final

BOUNDED_MULTI_AGENT_DELIVERY_EXECUTION_SCHEMA_VERSION: Final[str] = (
    "mission_control_bounded_multi_agent_delivery_execution_v1"
)
BOUNDED_MULTI_AGENT_DELIVERY_EXECUTION_RECORD_SCHEMA_VERSION: Final[str] = (
    "mission_control_bounded_multi_agent_delivery_execution_record_v1"
)
BOUNDED_MULTI_AGENT_DELIVERY_EXECUTION_FIX: Final[str] = "FIX 189"

MUTATION_PERFORMED_FIX_189: Final[bool] = False
BOUNDED_WORK_PERFORMED_FIX_189: Final[bool] = True
AGENT_EXECUTION_AUTHORITY_FIX_189: Final[bool] = False
MERGE_AUTHORITY_FIX_189: Final[bool] = False
DEPLOY_AUTHORITY_FIX_189: Final[bool] = False
RAILWAY_AUTHORITY_FIX_189: Final[bool] = False
PROVIDER_AUTHORITY_FIX_189: Final[bool] = False
GATE_BYPASS_ENABLED_FIX_189: Final[bool] = False
AUTONOMOUS_APPROVAL_ENABLED_FIX_189: Final[bool] = False
GOVERNANCE_MUTATION_PERFORMED_FIX_189: Final[bool] = False

BOUNDED_MULTI_AGENT_DELIVERY_EXECUTION_ROUTE_ID: Final[str] = (
    "mission_control_bounded_multi_agent_delivery_execution"
)

BOUNDED_MULTI_AGENT_DELIVERY_EXECUTION_ORIGIN: Final[str] = (
    "mission_control_bounded_multi_agent_delivery_execution"
)

BOUNDED_MULTI_AGENT_DELIVERY_EXECUTION_INVARIANT: Final[str] = (
    "bounded_multi_agent_delivery_execution_performs_bounded_agent_work_within_authorized_envelope_without_agent_execution_authority_or_gate_bypass"
)

AGENT_EXECUTION_ROLE_IDS: Final[tuple[str, ...]] = (
    "planner_agent",
    "delivery_agent",
    "verification_agent",
    "diff_audit_agent",
    "risk_agent",
)

AGENT_EXECUTION_PIPELINE_ORDER: Final[tuple[str, ...]] = (
    "planner_agent",
    "delivery_agent",
    "verification_agent",
    "diff_audit_agent",
    "risk_agent",
)

AGENT_EXECUTION_CATALOG: Final[tuple[tuple[str, str, str], ...]] = (
    ("planner_agent", "PlannerAgent", "Implementation plan generation and task decomposition"),
    ("delivery_agent", "DeliveryAgent", "Patch generation within authorization envelope"),
    ("verification_agent", "VerificationAgent", "Verification package and execution planning"),
    ("diff_audit_agent", "DiffAuditAgent", "Patch review, scope drift, blast radius analysis"),
    ("risk_agent", "RiskAgent", "Risk scoring and authorization boundary checks"),
)

AGENT_EXECUTION_PIPELINE_STATES: Final[tuple[str, ...]] = (
    "BLOCKED",
    "READY",
    "PLANNER_RUNNING",
    "PLANNER_COMPLETE",
    "DELIVERY_RUNNING",
    "DELIVERY_COMPLETE",
    "VERIFICATION_RUNNING",
    "VERIFICATION_COMPLETE",
    "DIFF_AUDIT_RUNNING",
    "DIFF_AUDIT_COMPLETE",
    "RISK_RUNNING",
    "RISK_COMPLETE",
    "PIPELINE_COMPLETE",
)

ALLOWED_AGENT_WORK: Final[tuple[str, ...]] = (
    "planning",
    "patch_generation",
    "verification_preparation",
    "diff_analysis",
    "risk_analysis",
)

FORBIDDEN_AGENT_WORK: Final[tuple[str, ...]] = (
    "merge",
    "deploy",
    "railway_mutation",
    "provider_mutation",
    "production_actions",
    "gate_bypass",
    "autonomous_approval",
)

BOUNDED_MULTI_AGENT_DELIVERY_EXECUTION_RECORD_KINDS: Final[tuple[str, ...]] = (
    "agent_execution_receipt",
    "execution_artifact",
    "pipeline_transition",
    "execution_note",
    "forbidden_execution_note",
    "bounded_multi_agent_delivery_execution_record",
)

BOUNDED_MULTI_AGENT_DELIVERY_EXECUTION_PRINCIPLES: Final[tuple[tuple[str, str], ...]] = (
    ("authorization_required", "Agent execution requires FIX 170 authorized envelope."),
    ("work_packages_required", "Execution packages compose FIX 168 work packages."),
    ("participation_required", "Execution requires FIX 171 bounded participation context."),
    ("agents_work_gates_decide", "Agents perform bounded work; existing frozen gates decide."),
    ("humans_authorize", "Human authorization and admission remain required downstream."),
    ("no_agent_execution_authority", "Agent execution authority remains false."),
    ("no_hidden_paths", "All agent work routes through existing software delivery services."),
    ("no_authority_expansion", "Merge, deploy, Railway, and provider authority remain false."),
)

FORBIDDEN_EXECUTION_ACTIONS: Final[tuple[tuple[str, str], ...]] = (
    ("merge", "Agent execution never merges pull requests."),
    ("deploy", "Agent execution never deploys."),
    ("railway_mutation", "Agent execution never mutates Railway."),
    ("provider_mutation", "Agent execution never mutates external providers."),
    ("gate_bypass", "Agent execution never bypasses frozen gates."),
    ("autonomous_approval", "Agents never approve gates or human decisions."),
    ("agent_execution_authority", "Agents perform work — they do not gain execution authority."),
    ("hidden_execution_path", "No hidden execution paths outside governed services."),
)

BOUNDED_MULTI_AGENT_DELIVERY_EXECUTION_EXECUTABLE: Final[bool] = True

MAX_BOUNDED_MULTI_AGENT_DELIVERY_EXECUTION_CONTENT_LEN: Final[int] = 4000
MAX_PERSISTED_BOUNDED_MULTI_AGENT_DELIVERY_EXECUTION_RECORDS: Final[int] = 500

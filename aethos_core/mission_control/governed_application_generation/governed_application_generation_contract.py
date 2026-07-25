# SPDX-License-Identifier: Apache-2.0
"""FIX 250 — governed application generation contract."""

from __future__ import annotations

from typing import Final

GOVERNED_APPLICATION_GENERATION_SCHEMA_VERSION: Final[str] = (
    "mission_control_governed_application_generation_v1"
)
GOVERNED_APPLICATION_GENERATION_RECORD_SCHEMA_VERSION: Final[str] = (
    "mission_control_governed_application_generation_record_v1"
)
GOVERNED_APPLICATION_GENERATION_HANDOFF_SCHEMA_VERSION: Final[str] = (
    "mission_control_governed_application_generation_handoff_v1"
)
GOVERNED_APPLICATION_GENERATION_FIX: Final[str] = "FIX 250"

MUTATION_PERFORMED_FIX_250: Final[bool] = False
EXECUTION_PERFORMED_FIX_250: Final[bool] = False
APPLICATION_GENERATION_AUTHORITY_FIX_250: Final[bool] = False
REPOSITORY_CREATION_AUTHORITY_FIX_250: Final[bool] = False
GITHUB_MUTATION_AUTHORITY_FIX_250: Final[bool] = False
PROVIDER_AUTHORITY_FIX_250: Final[bool] = False
DEPLOYMENT_AUTHORITY_FIX_250: Final[bool] = False
CODE_GENERATION_AUTHORITY_FIX_250: Final[bool] = False
MERGE_AUTHORITY_FIX_250: Final[bool] = False
ROLLBACK_AUTHORITY_FIX_250: Final[bool] = False
INFRASTRUCTURE_MUTATION_AUTHORITY_FIX_250: Final[bool] = False
GATE_BYPASS_ENABLED_FIX_250: Final[bool] = False
GOVERNANCE_MUTATION_PERFORMED_FIX_250: Final[bool] = False
GOVERNED_APPLICATION_GENERATION_COMPOSES_EVIDENCE_ONLY_FIX_250: Final[bool] = True

GOVERNED_APPLICATION_GENERATION_ROUTE_ID: Final[str] = "mission_control_governed_application_generation"
GOVERNED_APPLICATION_GENERATION_ORIGIN: Final[str] = "mission_control_governed_application_generation"

GOVERNED_APPLICATION_GENERATION_INVARIANT: Final[str] = (
    "governed_application_generation_plans_product_creation_from_prd_without_application_generation_authority"
)

GENERATION_PIPELINE_STAGES: Final[tuple[str, ...]] = (
    "product_understanding",
    "architecture_generation",
    "repository_blueprint",
    "delivery_backlog_generation",
    "governed_repository_creation_plan",
    "existing_delivery_pipeline",
)

BOUNDED_GENERATION_AGENT_ROLES: Final[tuple[str, ...]] = (
    "planner_agent",
    "architecture_agent",
    "repository_agent",
    "verification_agent",
    "risk_agent",
    "synthesis_agent",
)

GENERATION_DECISION_KINDS: Final[tuple[str, ...]] = (
    "generation_decision_approve",
    "generation_decision_hold",
    "generation_decision_reject",
)

REQUIRED_GENERATION_EVIDENCE_IDS: Final[tuple[str, ...]] = (
    "prd_reference",
    "product_understanding",
    "architecture_package",
    "repository_blueprint",
    "delivery_backlog",
    "human_generation_decision",
)

GOVERNED_APPLICATION_GENERATION_RECORD_KINDS: Final[tuple[str, ...]] = (
    "prd_intake_note",
    "product_vision_note",
    "requirements_note",
    "constraints_note",
    "architecture_package_note",
    "repository_blueprint_note",
    "delivery_backlog_note",
    "generation_decision_approve",
    "generation_decision_hold",
    "generation_decision_reject",
    "agent_synthesis_note",
    "governed_application_generation_record",
)

GOVERNED_APPLICATION_GENERATION_PRINCIPLES: Final[tuple[tuple[str, str], ...]] = (
    ("generation_not_authority", "application_generation ≠ autonomous_authority."),
    ("capability_not_execution", "Generation is capability — authority remains human."),
    ("planning_only", "No repositories created and no code generated in FIX 250."),
    ("existing_pipeline", "Approved work feeds the existing Plan → Patch → Verify → PR pipeline."),
    ("generation_memory", "Persist PRDs, architecture, blueprints, and backlogs for evolution."),
    ("bounded_agents", "Planner, architecture, repository, verification, risk, and synthesis agents are bounded."),
    ("no_github_mutation", "Never mutate GitHub from generation layer."),
    ("no_provider_creation", "Never create providers from generation layer."),
    ("no_separate_execution_path", "No hidden execution path — one governed delivery pipeline."),
    ("intent_to_product", "Bridge repository intelligence to product creation from intent."),
)

FORBIDDEN_APPLICATION_GENERATION_ACTIONS: Final[tuple[tuple[str, str], ...]] = (
    ("repository_creation", "Never create repositories from generation layer."),
    ("provider_creation", "Never create providers from generation layer."),
    ("github_mutation", "Never mutate GitHub from generation layer."),
    ("code_generation", "Never generate implementation code autonomously in FIX 250."),
    ("merge_execution", "Never merge from generation layer."),
    ("deploy_execution", "Never deploy from generation layer."),
    ("rollback_execution", "Never rollback from generation layer."),
    ("infrastructure_mutation", "Never mutate infrastructure from generation layer."),
    ("production_mutation", "Never mutate production from generation layer."),
    ("gate_bypass", "Never bypass frozen governance gates."),
)

GOVERNED_APPLICATION_GENERATION_EXECUTABLE: Final[bool] = False
GOVERNED_APPLICATION_GENERATION_HANDOFF_EXECUTABLE: Final[bool] = False

MAX_GOVERNED_APPLICATION_GENERATION_CONTENT_LEN: Final[int] = 8000
MAX_PERSISTED_GOVERNED_APPLICATION_GENERATION_RECORDS: Final[int] = 500

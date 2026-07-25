# SPDX-License-Identifier: Apache-2.0
"""FIX 280 — autonomous application lifecycle management contract."""

from __future__ import annotations

from typing import Final

AUTONOMOUS_APPLICATION_LIFECYCLE_MANAGEMENT_SCHEMA_VERSION: Final[str] = (
    "mission_control_autonomous_application_lifecycle_management_v1"
)
AUTONOMOUS_APPLICATION_LIFECYCLE_MANAGEMENT_RECORD_SCHEMA_VERSION: Final[str] = (
    "mission_control_autonomous_application_lifecycle_management_record_v1"
)
AUTONOMOUS_APPLICATION_LIFECYCLE_MANAGEMENT_FIX: Final[str] = "FIX 280"

MUTATION_PERFORMED_FIX_280: Final[bool] = False
EXECUTION_PERFORMED_FIX_280: Final[bool] = False
LIFECYCLE_MANAGEMENT_AUTHORITY_FIX_280: Final[bool] = False
AUTOMATIC_LIFECYCLE_EXECUTION_ENABLED_FIX_280: Final[bool] = False
REPOSITORY_MUTATION_AUTHORITY_FIX_280: Final[bool] = False
DEPLOYMENT_AUTHORITY_FIX_280: Final[bool] = False
ROLLBACK_AUTHORITY_FIX_280: Final[bool] = False
TRUST_MUTATION_AUTHORITY_FIX_280: Final[bool] = False
MERGE_AUTHORITY_FIX_280: Final[bool] = False
PROVIDER_MUTATION_AUTHORITY_FIX_280: Final[bool] = False
GATE_BYPASS_ENABLED_FIX_280: Final[bool] = False
GOVERNANCE_MUTATION_PERFORMED_FIX_280: Final[bool] = False
AUTONOMOUS_APPLICATION_LIFECYCLE_COMPOSES_EVIDENCE_ONLY_FIX_280: Final[bool] = True

AUTONOMOUS_APPLICATION_LIFECYCLE_MANAGEMENT_ROUTE_ID: Final[str] = (
    "mission_control_autonomous_application_lifecycle_management"
)
AUTONOMOUS_APPLICATION_LIFECYCLE_MANAGEMENT_ORIGIN: Final[str] = (
    "mission_control_autonomous_application_lifecycle_management"
)

AUTONOMOUS_APPLICATION_LIFECYCLE_MANAGEMENT_INVARIANT: Final[str] = (
    "autonomous_application_lifecycle_management_tracks_lifecycle_state_without_execution_authority"
)

LIFECYCLE_STAGES: Final[tuple[str, ...]] = (
    "concept",
    "product_design",
    "delivery",
    "deployment",
    "operations",
    "recovery",
    "evolution",
)

LIFECYCLE_HEALTH_DIMENSIONS: Final[tuple[str, ...]] = (
    "delivery",
    "operational",
    "governance",
    "evolution",
    "portfolio",
)

LIFECYCLE_RISK_DIMENSIONS: Final[tuple[str, ...]] = (
    "delivery",
    "operational",
    "governance",
    "architecture",
    "product",
)

HUMAN_LIFECYCLE_DECISION_KINDS: Final[tuple[str, ...]] = (
    "human_lifecycle_decision_approve",
    "human_lifecycle_decision_hold",
    "human_lifecycle_decision_reject",
    "human_lifecycle_decision_defer",
)

AUTONOMOUS_APPLICATION_LIFECYCLE_MANAGEMENT_RECORD_KINDS: Final[tuple[str, ...]] = (
    "concept_lifecycle_note",
    "design_lifecycle_note",
    "delivery_lifecycle_note",
    "deployment_lifecycle_note",
    "operations_lifecycle_note",
    "recovery_lifecycle_note",
    "evolution_lifecycle_note",
    "lifecycle_transition_note",
    *HUMAN_LIFECYCLE_DECISION_KINDS,
    "autonomous_application_lifecycle_management_record",
)

AUTONOMOUS_APPLICATION_LIFECYCLE_MANAGEMENT_PRINCIPLES: Final[tuple[tuple[str, str], ...]] = (
    ("lifecycle_not_execution", "Lifecycle management ≠ execution authority."),
    ("compose_only", "Composes FIX 250–270 and governed lifecycle capabilities without re-execution."),
    ("unified_model", "One lifecycle model spans concept through recovery and evolution."),
    ("humans_approve_transitions", "Humans approve lifecycle transitions — governed systems execute."),
    ("no_repository_mutation", "No repository mutation from lifecycle management layer."),
    ("no_deploy_rollback", "No deploy or rollback execution from lifecycle management."),
    ("no_trust_mutation", "Trust baselines are read-only lifecycle inputs."),
    ("single_system_of_record", "Lifecycle registries unify ideas, delivery, operations, and recovery."),
    ("advisory_opportunities", "Unified opportunity registry aggregates generation, evolution, stewardship."),
    ("memory_persistence", "Lifecycle memory persists events, transitions, and decisions."),
)

FORBIDDEN_LIFECYCLE_MANAGEMENT_ACTIONS: Final[tuple[tuple[str, str], ...]] = (
    ("code_execution", "Lifecycle management never executes code."),
    ("repository_mutation", "Lifecycle management never mutates repositories."),
    ("patch_execution", "Lifecycle management never executes patches."),
    ("pr_creation", "Lifecycle management never creates pull requests."),
    ("merge_execution", "Lifecycle management never merges."),
    ("deploy_execution", "Lifecycle management never deploys."),
    ("rollback_execution", "Lifecycle management never rollbacks."),
    ("provider_mutation", "Lifecycle management never mutates providers."),
    ("trust_mutation", "Lifecycle management never mutates trust baselines."),
    ("cross_repo_execution", "Lifecycle management never executes cross-repository changes."),
    ("automatic_lifecycle_execution", "Lifecycle management never auto-advances lifecycle stages."),
    ("gate_bypass", "Lifecycle management never bypasses frozen governance gates."),
)

AUTONOMOUS_APPLICATION_LIFECYCLE_MANAGEMENT_EXECUTABLE: Final[bool] = False

MAX_AUTONOMOUS_APPLICATION_LIFECYCLE_MANAGEMENT_CONTENT_LEN: Final[int] = 4000
MAX_PERSISTED_AUTONOMOUS_APPLICATION_LIFECYCLE_MANAGEMENT_RECORDS: Final[int] = 500

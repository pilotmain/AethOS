# SPDX-License-Identifier: Apache-2.0
"""FIX 270 — autonomous product stewardship contract."""

from __future__ import annotations

from typing import Final

from aethos_core.mission_control.independent_repository_trust_expansion.independent_repository_trust_expansion_contract import (
    ALL_REGISTRY_REPOSITORIES,
    PHASE_1_REPOSITORY,
    PHASE_2_REPOSITORY_ORDER,
)

AUTONOMOUS_PRODUCT_STEWARDSHIP_SCHEMA_VERSION: Final[str] = (
    "mission_control_autonomous_product_stewardship_v1"
)
AUTONOMOUS_PRODUCT_STEWARDSHIP_RECORD_SCHEMA_VERSION: Final[str] = (
    "mission_control_autonomous_product_stewardship_record_v1"
)
AUTONOMOUS_PRODUCT_STEWARDSHIP_FIX: Final[str] = "FIX 270"

MUTATION_PERFORMED_FIX_270: Final[bool] = False
EXECUTION_PERFORMED_FIX_270: Final[bool] = False
PRODUCT_STEWARDSHIP_AUTHORITY_FIX_270: Final[bool] = False
AUTOMATIC_IMPROVEMENT_ENABLED_FIX_270: Final[bool] = False
CROSS_REPO_EXECUTION_ENABLED_FIX_270: Final[bool] = False
REPOSITORY_MUTATION_AUTHORITY_FIX_270: Final[bool] = False
DEPLOYMENT_AUTHORITY_FIX_270: Final[bool] = False
TRUST_MUTATION_AUTHORITY_FIX_270: Final[bool] = False
MERGE_AUTHORITY_FIX_270: Final[bool] = False
PROVIDER_MUTATION_AUTHORITY_FIX_270: Final[bool] = False
GATE_BYPASS_ENABLED_FIX_270: Final[bool] = False
GOVERNANCE_MUTATION_PERFORMED_FIX_270: Final[bool] = False
AUTONOMOUS_PRODUCT_STEWARDSHIP_COMPOSES_EVIDENCE_ONLY_FIX_270: Final[bool] = True

AUTONOMOUS_PRODUCT_STEWARDSHIP_ROUTE_ID: Final[str] = "mission_control_autonomous_product_stewardship"
AUTONOMOUS_PRODUCT_STEWARDSHIP_ORIGIN: Final[str] = "mission_control_autonomous_product_stewardship"

AUTONOMOUS_PRODUCT_STEWARDSHIP_INVARIANT: Final[str] = (
    "autonomous_product_stewardship_observes_and_recommends_without_execution_authority"
)

PORTFOLIO_REPOSITORIES: Final[tuple[str, ...]] = ALL_REGISTRY_REPOSITORIES

REPOSITORY_DISPLAY_NAMES: Final[dict[str, str]] = {
    PHASE_1_REPOSITORY: "AethOS",
    PHASE_2_REPOSITORY_ORDER[0]: "PilotOS UI",
    PHASE_2_REPOSITORY_ORDER[1]: "Atlas Trader",
    PHASE_2_REPOSITORY_ORDER[2]: "Nexora",
}

STEWARDSHIP_DOMAINS: Final[tuple[str, ...]] = (
    "product_health",
    "engineering",
    "operational",
    "governance",
    "portfolio",
)

STEWARDSHIP_PRIORITY_TIERS: Final[tuple[str, ...]] = (
    "CRITICAL",
    "HIGH",
    "MEDIUM",
    "LOW",
    "DEFER",
)

HUMAN_STEWARDSHIP_DECISION_KINDS: Final[tuple[str, ...]] = (
    "human_stewardship_decision_approve",
    "human_stewardship_decision_hold",
    "human_stewardship_decision_reject",
    "human_stewardship_decision_defer",
)

AUTONOMOUS_PRODUCT_STEWARDSHIP_RECORD_KINDS: Final[tuple[str, ...]] = (
    "product_health_observation",
    "engineering_stewardship_observation",
    "operational_stewardship_observation",
    "governance_stewardship_observation",
    "portfolio_stewardship_observation",
    "stewardship_opportunity_note",
    "stewardship_backlog_note",
    *HUMAN_STEWARDSHIP_DECISION_KINDS,
    "autonomous_product_stewardship_record",
)

AUTONOMOUS_PRODUCT_STEWARDSHIP_PRINCIPLES: Final[tuple[tuple[str, str], ...]] = (
    ("stewardship_not_execution", "Product stewardship ≠ execution authority."),
    ("compose_only", "Composes FIX 261, 260, 250, 240, 189–191, and trust baselines without re-execution."),
    ("continuous_observe", "Steward continuously observes — never auto-implements."),
    ("humans_approve", "AethOS recommends — humans approve — governed delivery executes."),
    ("no_repository_mutation", "No repository mutation from stewardship layer."),
    ("no_code_generation", "No code generation or patch execution from stewardship."),
    ("no_cross_repo_execution", "Cross-repository execution authority remains false."),
    ("no_trust_mutation", "Trust baselines are read-only inputs — never mutated."),
    ("no_deployment_authority", "Deployment authority remains false from stewardship."),
    ("memory_persistence", "Stewardship memory persists observations and decision history."),
)

FORBIDDEN_PRODUCT_STEWARDSHIP_ACTIONS: Final[tuple[tuple[str, str], ...]] = (
    ("code_generation", "Stewardship never generates code."),
    ("repository_mutation", "Stewardship never mutates repositories."),
    ("patch_execution", "Stewardship never executes patches."),
    ("pr_creation", "Stewardship never creates pull requests."),
    ("merge", "Stewardship never merges."),
    ("deploy", "Stewardship never deploys."),
    ("rollback", "Stewardship never rollbacks."),
    ("provider_mutation", "Stewardship never mutates providers."),
    ("trust_mutation", "Stewardship never mutates trust baselines."),
    ("cross_repo_execution", "Stewardship never executes cross-repository changes."),
    ("automatic_improvement", "Stewardship never auto-implements improvements."),
    ("gate_bypass", "Stewardship never bypasses frozen governance gates."),
)

AUTONOMOUS_PRODUCT_STEWARDSHIP_EXECUTABLE: Final[bool] = False

MAX_AUTONOMOUS_PRODUCT_STEWARDSHIP_CONTENT_LEN: Final[int] = 4000
MAX_PERSISTED_AUTONOMOUS_PRODUCT_STEWARDSHIP_RECORDS: Final[int] = 500

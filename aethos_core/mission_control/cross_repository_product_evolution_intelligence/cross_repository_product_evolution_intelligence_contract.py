# SPDX-License-Identifier: Apache-2.0
"""FIX 261 — cross-repository product evolution intelligence contract."""

from __future__ import annotations

from typing import Final

from aethos_core.mission_control.independent_repository_trust_expansion.independent_repository_trust_expansion_contract import (
    ALL_REGISTRY_REPOSITORIES,
    PHASE_1_REPOSITORY,
    PHASE_2_REPOSITORY_ORDER,
)

CROSS_REPOSITORY_PRODUCT_EVOLUTION_INTELLIGENCE_SCHEMA_VERSION: Final[str] = (
    "mission_control_cross_repository_product_evolution_intelligence_v1"
)
CROSS_REPOSITORY_PRODUCT_EVOLUTION_INTELLIGENCE_RECORD_SCHEMA_VERSION: Final[str] = (
    "mission_control_cross_repository_product_evolution_intelligence_record_v1"
)
CROSS_REPOSITORY_PRODUCT_EVOLUTION_INTELLIGENCE_FIX: Final[str] = "FIX 261"

MUTATION_PERFORMED_FIX_261: Final[bool] = False
EXECUTION_PERFORMED_FIX_261: Final[bool] = False
PRODUCT_EVOLUTION_AUTHORITY_FIX_261: Final[bool] = False
AUTOMATIC_IMPROVEMENT_ENABLED_FIX_261: Final[bool] = False
CROSS_REPO_EXECUTION_ENABLED_FIX_261: Final[bool] = False
REPOSITORY_MUTATION_AUTHORITY_FIX_261: Final[bool] = False
TRUST_MUTATION_AUTHORITY_FIX_261: Final[bool] = False
MERGE_AUTHORITY_FIX_261: Final[bool] = False
DEPLOY_AUTHORITY_FIX_261: Final[bool] = False
PROVIDER_MUTATION_AUTHORITY_FIX_261: Final[bool] = False
GATE_BYPASS_ENABLED_FIX_261: Final[bool] = False
GOVERNANCE_MUTATION_PERFORMED_FIX_261: Final[bool] = False
CROSS_REPOSITORY_PRODUCT_EVOLUTION_COMPOSES_EVIDENCE_ONLY_FIX_261: Final[bool] = True

CROSS_REPOSITORY_PRODUCT_EVOLUTION_INTELLIGENCE_ROUTE_ID: Final[str] = (
    "mission_control_cross_repository_product_evolution_intelligence"
)
CROSS_REPOSITORY_PRODUCT_EVOLUTION_INTELLIGENCE_ORIGIN: Final[str] = (
    "mission_control_cross_repository_product_evolution_intelligence"
)

CROSS_REPOSITORY_PRODUCT_EVOLUTION_INTELLIGENCE_INVARIANT: Final[str] = (
    "cross_repository_product_evolution_intelligence_identifies_opportunities_without_execution_authority"
)

PORTFOLIO_REPOSITORIES: Final[tuple[str, ...]] = ALL_REGISTRY_REPOSITORIES

REPOSITORY_DISPLAY_NAMES: Final[dict[str, str]] = {
    PHASE_1_REPOSITORY: "AethOS",
    PHASE_2_REPOSITORY_ORDER[0]: "PilotOS UI",
    PHASE_2_REPOSITORY_ORDER[1]: "Atlas Trader",
    PHASE_2_REPOSITORY_ORDER[2]: "Nexora",
}

EVOLUTION_DOMAINS: Final[tuple[str, ...]] = (
    "feature",
    "quality",
    "architecture",
    "operational",
    "ux",
)

EVOLUTION_PRIORITY_TIERS: Final[tuple[str, ...]] = (
    "CRITICAL",
    "HIGH",
    "MEDIUM",
    "LOW",
    "DEFER",
)

HUMAN_EVOLUTION_DECISION_KINDS: Final[tuple[str, ...]] = (
    "human_evolution_decision_approve",
    "human_evolution_decision_hold",
    "human_evolution_decision_reject",
    "human_evolution_decision_defer",
)

CROSS_REPOSITORY_PRODUCT_EVOLUTION_INTELLIGENCE_RECORD_KINDS: Final[tuple[str, ...]] = (
    "feature_evolution_note",
    "quality_evolution_note",
    "architecture_evolution_note",
    "operational_evolution_note",
    "ux_evolution_note",
    "opportunity_graph_note",
    "evolution_backlog_note",
    *HUMAN_EVOLUTION_DECISION_KINDS,
    "cross_repository_product_evolution_intelligence_record",
)

CROSS_REPOSITORY_PRODUCT_EVOLUTION_INTELLIGENCE_PRINCIPLES: Final[tuple[tuple[str, str], ...]] = (
    ("evolution_not_execution", "Product evolution intelligence ≠ execution authority."),
    ("compose_only", "Composes FIX 240, 250, 260, 189–191, and trust baselines without re-execution."),
    ("humans_decide", "AethOS identifies opportunities — humans decide what to pursue."),
    ("governed_delivery_only", "Approved opportunities feed governed delivery — never auto-execute."),
    ("no_repository_mutation", "No repository mutation from evolution intelligence layer."),
    ("no_code_generation", "No code generation or patch execution from evolution intelligence."),
    ("no_cross_repo_authority", "Cross-repository execution authority remains false."),
    ("no_trust_mutation", "Trust baselines are read-only inputs — never mutated."),
    ("portfolio_wide", "Analyzes all conditionally trusted repositories together."),
    ("advisory_backlog", "Evolution backlog and priority matrix are advisory only."),
)

FORBIDDEN_PRODUCT_EVOLUTION_ACTIONS: Final[tuple[tuple[str, str], ...]] = (
    ("code_generation", "Evolution intelligence never generates code."),
    ("patch_execution", "Evolution intelligence never executes patches."),
    ("repository_mutation", "Evolution intelligence never mutates repositories."),
    ("cross_repo_mutation", "Evolution intelligence never mutates across repositories."),
    ("pr_creation", "Evolution intelligence never creates pull requests."),
    ("merge", "Evolution intelligence never merges."),
    ("deploy", "Evolution intelligence never deploys."),
    ("rollback", "Evolution intelligence never rollbacks."),
    ("provider_mutation", "Evolution intelligence never mutates providers."),
    ("trust_mutation", "Evolution intelligence never mutates trust baselines."),
    ("automatic_improvement", "Evolution intelligence never auto-implements improvements."),
    ("gate_bypass", "Evolution intelligence never bypasses frozen governance gates."),
)

CROSS_REPOSITORY_PRODUCT_EVOLUTION_INTELLIGENCE_EXECUTABLE: Final[bool] = False

MAX_CROSS_REPOSITORY_PRODUCT_EVOLUTION_INTELLIGENCE_CONTENT_LEN: Final[int] = 4000
MAX_PERSISTED_CROSS_REPOSITORY_PRODUCT_EVOLUTION_INTELLIGENCE_RECORDS: Final[int] = 500

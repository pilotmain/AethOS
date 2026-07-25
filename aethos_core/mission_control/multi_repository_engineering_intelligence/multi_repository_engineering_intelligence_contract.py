# SPDX-License-Identifier: Apache-2.0
"""FIX 260 — multi-repository engineering intelligence contract."""

from __future__ import annotations

from typing import Final

from aethos_core.mission_control.independent_repository_trust_expansion.independent_repository_trust_expansion_contract import (
    ALL_REGISTRY_REPOSITORIES,
    PHASE_1_REPOSITORY,
    PHASE_2_REPOSITORY_ORDER,
)

MULTI_REPOSITORY_ENGINEERING_INTELLIGENCE_SCHEMA_VERSION: Final[str] = (
    "mission_control_multi_repository_engineering_intelligence_v1"
)
MULTI_REPOSITORY_ENGINEERING_INTELLIGENCE_RECORD_SCHEMA_VERSION: Final[str] = (
    "mission_control_multi_repository_engineering_intelligence_record_v1"
)
MULTI_REPOSITORY_ENGINEERING_INTELLIGENCE_FIX: Final[str] = "FIX 260"

MUTATION_PERFORMED_FIX_260: Final[bool] = False
EXECUTION_PERFORMED_FIX_260: Final[bool] = False
PORTFOLIO_AUTHORITY_FIX_260: Final[bool] = False
CROSS_REPO_AUTHORITY_FIX_260: Final[bool] = False
PROGRAM_DELIVERY_AUTHORITY_FIX_260: Final[bool] = False
MERGE_AUTHORITY_FIX_260: Final[bool] = False
DEPLOY_AUTHORITY_FIX_260: Final[bool] = False
PROVIDER_MUTATION_AUTHORITY_FIX_260: Final[bool] = False
GATE_BYPASS_ENABLED_FIX_260: Final[bool] = False
GOVERNANCE_MUTATION_PERFORMED_FIX_260: Final[bool] = False
MULTI_REPOSITORY_ENGINEERING_INTELLIGENCE_COMPOSES_EVIDENCE_ONLY_FIX_260: Final[bool] = True

MULTI_REPOSITORY_ENGINEERING_INTELLIGENCE_ROUTE_ID: Final[str] = (
    "mission_control_multi_repository_engineering_intelligence"
)
MULTI_REPOSITORY_ENGINEERING_INTELLIGENCE_ORIGIN: Final[str] = (
    "mission_control_multi_repository_engineering_intelligence"
)

MULTI_REPOSITORY_ENGINEERING_INTELLIGENCE_INVARIANT: Final[str] = (
    "multi_repository_engineering_intelligence_composes_portfolio_visibility_without_cross_repo_authority"
)

PORTFOLIO_REPOSITORIES: Final[tuple[str, ...]] = ALL_REGISTRY_REPOSITORIES

REPOSITORY_DISPLAY_NAMES: Final[dict[str, str]] = {
    PHASE_1_REPOSITORY: "AethOS",
    PHASE_2_REPOSITORY_ORDER[0]: "PilotOS UI",
    PHASE_2_REPOSITORY_ORDER[1]: "Atlas Trader",
    PHASE_2_REPOSITORY_ORDER[2]: "Nexora",
}

ENGINEERING_HEALTH_TIERS: Final[tuple[str, ...]] = (
    "EXCELLENT",
    "HEALTHY",
    "WATCH",
    "AT_RISK",
    "UNPROVEN",
)

PROGRAM_DELIVERY_STAGES: Final[tuple[str, ...]] = (
    "plan",
    "patch",
    "verify",
    "pr_open",
    "merge",
    "deploy",
    "monitor",
    "rollback",
)

MULTI_REPOSITORY_ENGINEERING_INTELLIGENCE_RECORD_KINDS: Final[tuple[str, ...]] = (
    "portfolio_observation_note",
    "cross_repo_dependency_note",
    "program_delivery_note",
    "engineering_health_note",
    "multi_repository_intelligence_record",
)

MULTI_REPOSITORY_ENGINEERING_INTELLIGENCE_PRINCIPLES: Final[tuple[tuple[str, str], ...]] = (
    ("portfolio_not_authority", "portfolio visibility ≠ cross-repository authority."),
    ("compose_only", "Composes FIX 191, 187, 240, and lifecycle evidence without re-execution."),
    ("no_trust_inheritance", "Repository trust remains independent per FIX 187."),
    ("advisory_dependencies", "Cross-repo dependency links are advisory only."),
    ("program_visibility", "Program delivery visibility reports status — does not orchestrate delivery."),
    ("health_scoring_advisory", "Engineering health scores are advisory — not operational authority."),
    ("no_provider_mutation", "No provider mutation from portfolio intelligence layer."),
    ("no_merge_deploy", "No merge, deploy, or rollback from portfolio intelligence layer."),
    ("evidence_first", "Portfolio intelligence requires stored evidence per repository."),
    ("scale_after_trust", "Multi-repo intelligence informs scaling — does not grant scaling authority."),
)

FORBIDDEN_MULTI_REPOSITORY_INTELLIGENCE_ACTIONS: Final[tuple[tuple[str, str], ...]] = (
    ("cross_repo_authority", "Never exercise cross-repository operational authority."),
    ("portfolio_orchestration", "Never orchestrate delivery across repositories autonomously."),
    ("trust_transfer", "Never inherit trust between repositories."),
    ("provider_mutation", "Never mutate providers from portfolio layer."),
    ("merge_execution", "Never merge from portfolio layer."),
    ("deploy_execution", "Never deploy from portfolio layer."),
    ("rollback_execution", "Never rollback from portfolio layer."),
    ("hidden_program_path", "Never use hidden cross-repo execution paths."),
    ("gate_bypass", "Never bypass frozen governance gates."),
)

MULTI_REPOSITORY_ENGINEERING_INTELLIGENCE_EXECUTABLE: Final[bool] = False

MAX_MULTI_REPOSITORY_ENGINEERING_INTELLIGENCE_CONTENT_LEN: Final[int] = 4000
MAX_PERSISTED_MULTI_REPOSITORY_ENGINEERING_INTELLIGENCE_RECORDS: Final[int] = 500

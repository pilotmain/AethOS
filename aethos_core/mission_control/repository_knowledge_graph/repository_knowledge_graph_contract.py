# SPDX-License-Identifier: Apache-2.0
"""FIX 240 — repository knowledge graph contract."""

from __future__ import annotations

from typing import Final

from aethos_core.mission_control.independent_repository_trust_expansion.independent_repository_trust_expansion_contract import (
    ALL_REGISTRY_REPOSITORIES,
    PHASE_1_REPOSITORY,
    PHASE_2_REPOSITORY_ORDER,
)

REPOSITORY_KNOWLEDGE_GRAPH_SCHEMA_VERSION: Final[str] = "mission_control_repository_knowledge_graph_v1"
REPOSITORY_KNOWLEDGE_GRAPH_RECORD_SCHEMA_VERSION: Final[str] = (
    "mission_control_repository_knowledge_graph_record_v1"
)
REPOSITORY_KNOWLEDGE_GRAPH_FIX: Final[str] = "FIX 240"

MUTATION_PERFORMED_FIX_240: Final[bool] = False
EXECUTION_PERFORMED_FIX_240: Final[bool] = False
REPOSITORY_AUTHORITY_FIX_240: Final[bool] = False
CODE_MODIFICATION_AUTHORITY_FIX_240: Final[bool] = False
CROSS_REPO_AUTHORITY_FIX_240: Final[bool] = False
KNOWLEDGE_GRAPH_EXECUTION_FIX_240: Final[bool] = False
MERGE_AUTHORITY_FIX_240: Final[bool] = False
DEPLOY_AUTHORITY_FIX_240: Final[bool] = False
ROLLBACK_AUTHORITY_FIX_240: Final[bool] = False
PROVIDER_MUTATION_AUTHORITY_FIX_240: Final[bool] = False
GATE_BYPASS_ENABLED_FIX_240: Final[bool] = False
GOVERNANCE_MUTATION_PERFORMED_FIX_240: Final[bool] = False
REPOSITORY_KNOWLEDGE_GRAPH_COMPOSES_EVIDENCE_ONLY_FIX_240: Final[bool] = True

REPOSITORY_KNOWLEDGE_GRAPH_ROUTE_ID: Final[str] = "mission_control_repository_knowledge_graph"
REPOSITORY_KNOWLEDGE_GRAPH_ORIGIN: Final[str] = "mission_control_repository_knowledge_graph"

REPOSITORY_KNOWLEDGE_GRAPH_INVARIANT: Final[str] = (
    "repository_knowledge_graph_builds_engineering_intelligence_from_stored_evidence_without_repository_authority"
)

PHASE_1_KNOWLEDGE_REPOSITORIES: Final[tuple[str, ...]] = ALL_REGISTRY_REPOSITORIES

REPOSITORY_DISPLAY_NAMES: Final[dict[str, str]] = {
    PHASE_1_REPOSITORY: "AethOS",
    PHASE_2_REPOSITORY_ORDER[0]: "PilotOS UI",
    PHASE_2_REPOSITORY_ORDER[1]: "Atlas Trader",
    PHASE_2_REPOSITORY_ORDER[2]: "Nexora",
}

ARCHITECTURE_NODE_KINDS: Final[tuple[str, ...]] = (
    "application",
    "service",
    "library",
    "package",
    "module",
    "boundary",
)

RISK_TIERS: Final[tuple[str, ...]] = (
    "low",
    "medium",
    "high",
    "critical",
)

REQUIRED_INTELLIGENCE_EVIDENCE_IDS: Final[tuple[str, ...]] = (
    "repository_reference",
    "architecture_graph",
    "dependency_registry",
    "ownership_registry",
    "historical_change_signals",
    "risk_profile",
)

REPOSITORY_KNOWLEDGE_GRAPH_RECORD_KINDS: Final[tuple[str, ...]] = (
    "architecture_discovery_note",
    "dependency_mapping_note",
    "ownership_record_note",
    "historical_pattern_note",
    "change_impact_annotation",
    "repository_intelligence_note",
    "repository_knowledge_graph_record",
)

REPOSITORY_KNOWLEDGE_GRAPH_PRINCIPLES: Final[tuple[tuple[str, str], ...]] = (
    ("intelligence_not_authority", "repository_intelligence ≠ repository_authority."),
    ("understanding_not_execution", "Understanding is not execution — all outputs advisory."),
    ("compose_delivery_evidence", "Composes issue plans, verification, and lifecycle evidence."),
    ("repository_memory", "Persist discoveries for reuse across future issues."),
    ("cross_repo_advisory", "Cross-repository links remain advisory — no cross-repo authority."),
    ("analysis_only", "Knowledge graph generation is analysis only."),
    ("no_code_modification", "Never modify code from intelligence layer."),
    ("no_patch_or_pr", "Never generate patches or open PRs from intelligence layer."),
    ("no_operational_execution", "Never merge, deploy, or rollback from intelligence layer."),
    ("foundational_input", "Repository intelligence informs later delivery decisions."),
)

FORBIDDEN_KNOWLEDGE_GRAPH_ACTIONS: Final[tuple[tuple[str, str], ...]] = (
    ("code_modification", "Never modify code from knowledge graph layer."),
    ("patch_generation", "Never generate patches from knowledge graph layer."),
    ("pr_creation", "Never create pull requests from knowledge graph layer."),
    ("merge_execution", "Never merge from knowledge graph layer."),
    ("deploy_execution", "Never deploy from knowledge graph layer."),
    ("rollback_execution", "Never rollback from knowledge graph layer."),
    ("provider_mutation", "Never mutate providers from knowledge graph layer."),
    ("cross_repo_authority", "Never exercise cross-repository authority."),
    ("hidden_execution", "Never use hidden execution paths from intelligence layer."),
    ("gate_bypass", "Never bypass frozen governance gates."),
)

DEFAULT_ARCHITECTURE_BY_REPOSITORY: Final[dict[str, tuple[tuple[str, str, str], ...]]] = {
    PHASE_1_REPOSITORY: (
        ("aethos-core", "service", "aethos_core/"),
        ("mission-control", "module", "aethos_core/mission_control/"),
        ("software-delivery", "module", "aethos_core/software_delivery/"),
        ("web-app", "application", "web/"),
        ("tests", "library", "tests/"),
        ("docs", "boundary", "docs/"),
    ),
    PHASE_2_REPOSITORY_ORDER[0]: (
        ("pilotos-ui-app", "application", "apps/"),
        ("pilotos-ui-packages", "package", "packages/"),
        ("pilotos-ui-web", "application", "web/"),
    ),
    PHASE_2_REPOSITORY_ORDER[1]: (
        ("atlas-trader-core", "service", "src/"),
        ("atlas-trader-api", "service", "api/"),
        ("atlas-trader-web", "application", "web/"),
    ),
    PHASE_2_REPOSITORY_ORDER[2]: (
        ("nexora-monorepo-apps", "application", "apps/"),
        ("nexora-monorepo-packages", "package", "packages/"),
        ("nexora-monorepo-services", "service", "services/"),
    ),
}

DEFAULT_DEPENDENCIES_BY_REPOSITORY: Final[dict[str, tuple[tuple[str, str, str], ...]]] = {
    PHASE_1_REPOSITORY: (
        ("web-app", "aethos-core", "internal"),
        ("mission-control", "software-delivery", "internal"),
        ("software-delivery", "aethos-core", "internal"),
    ),
    PHASE_2_REPOSITORY_ORDER[0]: (
        ("pilotos-ui-app", "pilotos-ui-packages", "internal"),
        ("pilotos-ui-web", "pilotos-ui-packages", "internal"),
    ),
    PHASE_2_REPOSITORY_ORDER[1]: (
        ("atlas-trader-web", "atlas-trader-api", "internal"),
        ("atlas-trader-api", "atlas-trader-core", "internal"),
    ),
    PHASE_2_REPOSITORY_ORDER[2]: (
        ("nexora-monorepo-apps", "nexora-monorepo-packages", "internal"),
        ("nexora-monorepo-services", "nexora-monorepo-packages", "internal"),
    ),
}

DEFAULT_OWNERSHIP_BY_REPOSITORY: Final[dict[str, tuple[tuple[str, str, str], ...]]] = {
    PHASE_1_REPOSITORY: (
        ("mission-control", "platform-engineering", "maintainer"),
        ("software-delivery", "delivery-engineering", "maintainer"),
        ("web-app", "frontend-platform", "maintainer"),
    ),
    PHASE_2_REPOSITORY_ORDER[0]: (("pilotos-ui-app", "pilotos-ui-team", "owner"),),
    PHASE_2_REPOSITORY_ORDER[1]: (("atlas-trader-core", "atlas-trading-team", "owner"),),
    PHASE_2_REPOSITORY_ORDER[2]: (("nexora-monorepo-apps", "nexora-platform-team", "owner"),),
}

REPOSITORY_KNOWLEDGE_GRAPH_EXECUTABLE: Final[bool] = False

MAX_REPOSITORY_KNOWLEDGE_GRAPH_CONTENT_LEN: Final[int] = 4000
MAX_PERSISTED_REPOSITORY_KNOWLEDGE_GRAPH_RECORDS: Final[int] = 500

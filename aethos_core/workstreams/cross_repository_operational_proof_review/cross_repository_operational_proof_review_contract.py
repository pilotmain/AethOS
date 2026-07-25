# SPDX-License-Identifier: Apache-2.0
"""Cross-repository operational proof review contract."""

from __future__ import annotations

from typing import Final

from aethos_core.mission_control.cross_repository_multi_agent_delivery_validation.cross_repository_multi_agent_delivery_validation_contract import (
    REPOSITORY_DISPLAY_NAMES,
)
from aethos_core.mission_control.independent_repository_trust_expansion.independent_repository_trust_expansion_contract import (
    ALL_REGISTRY_REPOSITORIES,
    PHASE_1_REPOSITORY,
    PHASE_2_REPOSITORY_ORDER,
)

CROSS_REPOSITORY_OPERATIONAL_PROOF_REVIEW_ID: Final[str] = "CROSS_REPOSITORY_OPERATIONAL_PROOF_REVIEW"
CROSS_REPOSITORY_OPERATIONAL_PROOF_REVIEW_SCHEMA_VERSION: Final[str] = (
    "cross_repository_operational_proof_review_v1"
)

REVIEW_REPOSITORIES: Final[tuple[str, ...]] = ALL_REGISTRY_REPOSITORIES
REPOSITORY_LABELS: Final[dict[str, str]] = {
    PHASE_1_REPOSITORY: REPOSITORY_DISPLAY_NAMES.get(PHASE_1_REPOSITORY, "AethOS"),
    PHASE_2_REPOSITORY_ORDER[0]: "PilotOS UI",
    PHASE_2_REPOSITORY_ORDER[1]: "Atlas Trader",
    PHASE_2_REPOSITORY_ORDER[2]: "Nexora",
}

REVIEW_AREAS: Final[tuple[str, ...]] = (
    "review_area_1_repository_trust_baselines",
    "review_area_2_pilot_completion",
    "review_area_3_evidence_density",
    "review_area_4_verification_quality",
    "review_area_5_throughput",
    "review_area_6_cross_repository_consistency",
    "review_area_7_executive_visibility",
    "review_area_8_trust_generalization",
    "review_area_9_remaining_gaps",
    "review_area_10_strategic_recommendation",
)

TRUST_GENERALIZATION_LEVELS: Final[tuple[str, ...]] = (
    "NOT_PROVEN",
    "PARTIALLY_PROVEN",
    "PROVEN_WITH_LIMITATIONS",
    "PROVEN",
)

STRATEGIC_OPTIONS: Final[tuple[str, ...]] = (
    "option_a_expand_operational_proof",
    "option_b_expand_provider_coverage",
    "option_c_limited_external_customer_validation",
    "option_d_revisit_architecture",
)

EXECUTIVE_FIX_MODULES: Final[tuple[str, ...]] = (
    "FIX 260",
    "FIX 324",
    "FIX 325",
    "FIX 326",
    "FIX 327",
    "FIX 328",
    "FIX 329",
    "FIX 330",
)

PROGRAM_NON_GOALS: Final[tuple[str, ...]] = (
    "no_new_intelligence_modules",
    "no_new_governance_modules",
    "no_trust_mutations",
    "no_provider_expansion",
    "no_architecture_redesign",
)

CORE_PRINCIPLE: Final[str] = (
    "cross_repository_operational_review_evaluates_evidence_only_humans_determine_conclusions"
)

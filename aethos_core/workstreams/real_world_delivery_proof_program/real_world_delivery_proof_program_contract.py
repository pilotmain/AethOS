# SPDX-License-Identifier: Apache-2.0
"""WORKSTREAM_C1 / FIX 339 — real world delivery proof program contract."""

from __future__ import annotations

from typing import Any, Final

from aethos_core.mission_control.independent_repository_trust_expansion.independent_repository_trust_expansion_contract import (
    ALL_REGISTRY_REPOSITORIES,
    PHASE_1_REPOSITORY,
    PHASE_2_REPOSITORY_ORDER,
)

REAL_WORLD_DELIVERY_PROOF_PROGRAM_ID: Final[str] = "WORKSTREAM_C1"
REAL_WORLD_DELIVERY_PROOF_PROGRAM_FIX: Final[str] = "FIX 339"
REAL_WORLD_DELIVERY_PROOF_PROGRAM_SCHEMA_VERSION: Final[str] = (
    "workstream_real_world_delivery_proof_program_v1"
)
REAL_WORLD_DELIVERY_PROOF_PROGRAM_RECORD_SCHEMA_VERSION: Final[str] = (
    "workstream_real_world_delivery_proof_program_record_v1"
)

CORE_PRINCIPLE: Final[str] = (
    "operational_proof_measures_real_delivery_execution_without_authority_expansion"
)

MUTATION_PERFORMED_FIX_339: Final[bool] = False
EXECUTION_PERFORMED_FIX_339: Final[bool] = False
DELIVERY_AUTHORITY_FIX_339: Final[bool] = False
TRUST_MUTATION_AUTHORITY_FIX_339: Final[bool] = False
AUTHORITY_EXPANSION_FIX_339: Final[bool] = False
AUTOMATIC_PRODUCTION_PROMOTION_FIX_339: Final[bool] = False
GOVERNANCE_BYPASS_AUTHORITY_FIX_339: Final[bool] = False
GOVERNANCE_MUTATION_PERFORMED_FIX_339: Final[bool] = False
LOCAL_DELIVERY_PROOF_EXECUTABLE_FIX_339: Final[bool] = True

REAL_WORLD_DELIVERY_PROOF_PROGRAM_ROUTE_ID: Final[str] = (
    "workstream_real_world_delivery_proof_program"
)

REAL_WORLD_DELIVERY_PROOF_PROGRAM_INVARIANT: Final[str] = (
    "real_world_delivery_proof_without_authority_expansion_or_trust_promotion"
)

REAL_WORLD_DELIVERY_PROOF_PHASES: Final[tuple[str, ...]] = (
    "phase_1_candidate_selection",
    "phase_2_delivery_execution",
    "phase_3_verification",
    "phase_4_reliability_tracking",
    "phase_5_incident_tracking",
    "phase_6_operational_evidence",
    "phase_7_executive_visibility",
    "phase_8_trust_impact_analysis",
    "phase_9_human_review",
)

WAVE_1_REPOSITORIES: Final[tuple[str, ...]] = ALL_REGISTRY_REPOSITORIES

REPOSITORY_LABELS: Final[dict[str, str]] = {
    PHASE_1_REPOSITORY: "AethOS",
    PHASE_2_REPOSITORY_ORDER[0]: "PilotOS UI",
    PHASE_2_REPOSITORY_ORDER[1]: "Atlas Trader",
    PHASE_2_REPOSITORY_ORDER[2]: "Nexora",
}

WAVE_1_REPOSITORY_CONFIG: Final[dict[str, dict[str, Any]]] = {
    PHASE_1_REPOSITORY: {
        "display_name": "AethOS",
        "template_id": "generic_repository",
        "provider": "railway",
        "environment": "staging",
        "feature_prefix": "aethos-proof",
    },
    PHASE_2_REPOSITORY_ORDER[0]: {
        "display_name": "PilotOS UI",
        "template_id": "nextjs_web_app",
        "provider": "vercel",
        "environment": "preview",
        "feature_prefix": "pilotos-proof",
    },
    PHASE_2_REPOSITORY_ORDER[1]: {
        "display_name": "Atlas Trader",
        "template_id": "spring_boot_service",
        "provider": "railway",
        "environment": "staging",
        "feature_prefix": "atlas-proof",
    },
    PHASE_2_REPOSITORY_ORDER[2]: {
        "display_name": "Nexora",
        "template_id": "fullstack_reference",
        "provider": "railway",
        "environment": "staging",
        "feature_prefix": "nexora-proof",
    },
}

CANDIDATE_TYPES: Final[tuple[str, ...]] = (
    "low_risk_enhancement",
    "documentation_update",
    "bug_fix",
    "operational_improvement",
)

DELIVERY_PROOF_METRICS: Final[tuple[str, ...]] = (
    "successful_deliveries",
    "failed_deliveries",
    "deployments_completed",
    "deployments_verified",
    "human_interventions",
    "time_to_delivery_ms",
    "time_to_recovery_ms",
)

EXECUTIVE_FIX_MODULES: Final[tuple[str, ...]] = (
    "FIX 316",
    "FIX 324",
    "FIX 329",
    "FIX 330",
)

HUMAN_DELIVERY_PROOF_DECISION_KINDS: Final[tuple[str, ...]] = (
    "delivery_proof_review_approve",
    "delivery_proof_review_hold",
    "delivery_proof_review_reject",
    "delivery_proof_review_defer",
)

REAL_WORLD_DELIVERY_PROOF_RECORD_KINDS: Final[tuple[str, ...]] = (
    "delivery_proof_note",
    *HUMAN_DELIVERY_PROOF_DECISION_KINDS,
    "delivery_proof_executed_note",
    "real_world_delivery_proof_record",
)

PROGRAM_NON_GOALS: Final[tuple[str, ...]] = (
    "no_authority_expansion",
    "no_trust_promotion",
    "no_provider_expansion",
    "no_automatic_production_promotion",
    "no_governance_bypass",
    "no_new_intelligence_layers",
)

FORBIDDEN_DELIVERY_PROOF_ACTIONS: Final[tuple[tuple[str, str], ...]] = (
    ("authority_expansion", "Never expand delivery authority from proof program."),
    ("trust_promotion", "Never promote trust automatically from proof evidence."),
    ("governance_bypass", "Never bypass ET1–ET5 governance gates."),
    ("automatic_production_promotion", "Never promote to production automatically."),
    ("provider_expansion", "Never expand providers from proof program."),
)

MAX_REAL_WORLD_DELIVERY_PROOF_CONTENT_LEN: Final[int] = 8000
MAX_PERSISTED_REAL_WORLD_DELIVERY_PROOF_RECORDS: Final[int] = 500

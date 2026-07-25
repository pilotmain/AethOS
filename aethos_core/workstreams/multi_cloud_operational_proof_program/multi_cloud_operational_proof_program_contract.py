# SPDX-License-Identifier: Apache-2.0
"""WORKSTREAM_D2 / FIX 342 — multi-cloud operational proof program contract."""

from __future__ import annotations

from typing import Any, Final

MULTI_CLOUD_OPERATIONAL_PROOF_PROGRAM_ID: Final[str] = "WORKSTREAM_D2"
MULTI_CLOUD_OPERATIONAL_PROOF_PROGRAM_FIX: Final[str] = "FIX 342"
MULTI_CLOUD_OPERATIONAL_PROOF_PROGRAM_SCHEMA_VERSION: Final[str] = (
    "workstream_multi_cloud_operational_proof_program_v1"
)
MULTI_CLOUD_OPERATIONAL_PROOF_PROGRAM_RECORD_SCHEMA_VERSION: Final[str] = (
    "workstream_multi_cloud_operational_proof_program_record_v1"
)

CORE_PRINCIPLE: Final[str] = (
    "multi_cloud_proof_collects_evidence_without_granting_provider_authority"
)

MUTATION_PERFORMED_FIX_342: Final[bool] = False
EXECUTION_PERFORMED_FIX_342: Final[bool] = False
PROVIDER_AUTHORITY_FIX_342: Final[bool] = False
TRUST_MUTATION_AUTHORITY_FIX_342: Final[bool] = False
AUTHORITY_EXPANSION_FIX_342: Final[bool] = False
GOVERNANCE_BYPASS_AUTHORITY_FIX_342: Final[bool] = False
GOVERNANCE_MUTATION_PERFORMED_FIX_342: Final[bool] = False
LOCAL_MULTI_CLOUD_PROOF_EXECUTABLE_FIX_342: Final[bool] = True

MULTI_CLOUD_OPERATIONAL_PROOF_PROGRAM_ROUTE_ID: Final[str] = (
    "workstream_multi_cloud_operational_proof_program"
)

MULTI_CLOUD_OPERATIONAL_PROOF_PROGRAM_INVARIANT: Final[str] = (
    "multi_cloud_operational_proof_without_provider_authority_or_governance_change"
)

WAVE_1_PROVIDERS: Final[tuple[str, ...]] = ("AWS", "Kubernetes", "Azure", "GCP")
PHASE_1_PROOF_PROVIDERS: Final[tuple[str, ...]] = ("Railway", "Vercel")
ALL_PROOF_PROVIDERS: Final[tuple[str, ...]] = (*PHASE_1_PROOF_PROVIDERS, *WAVE_1_PROVIDERS)

MULTI_CLOUD_OPERATIONAL_PROOF_PHASES: Final[tuple[str, ...]] = (
    "phase_1_deployment_candidate_registry",
    "phase_2_multi_cloud_execution",
    "phase_3_verification",
    "phase_4_reliability_tracking",
    "phase_5_failure_intelligence",
    "phase_6_evidence_collection",
    "phase_7_comparative_analysis",
    "phase_8_executive_visibility",
    "phase_9_human_review",
)

PROVIDER_DEFAULT_SERVICES: Final[dict[str, str]] = {
    "Railway": "web-service",
    "Vercel": "nextjs-app",
    "AWS": "ECS",
    "Kubernetes": "deployment_rollout",
    "Azure": "App Service",
    "GCP": "Cloud Run",
}

PROVIDER_DEFAULT_ENVIRONMENTS: Final[dict[str, str]] = {
    "Railway": "staging",
    "Vercel": "preview",
    "AWS": "staging",
    "Kubernetes": "staging",
    "Azure": "staging",
    "GCP": "staging",
}

EXECUTIVE_FIX_MODULES: Final[tuple[str, ...]] = (
    "FIX 316",
    "FIX 324",
    "FIX 329",
    "FIX 330",
)

HUMAN_PROVIDER_PROOF_DECISION_KINDS: Final[tuple[str, ...]] = (
    "provider_proof_review_approve",
    "provider_proof_review_hold",
    "provider_proof_review_reject",
    "provider_proof_review_defer",
)

MULTI_CLOUD_OPERATIONAL_PROOF_RECORD_KINDS: Final[tuple[str, ...]] = (
    "provider_proof_note",
    *HUMAN_PROVIDER_PROOF_DECISION_KINDS,
    "provider_proof_executed_note",
    "multi_cloud_operational_proof_record",
)

PROGRAM_NON_GOALS: Final[tuple[str, ...]] = (
    "no_provider_authority",
    "no_trust_mutation",
    "no_governance_bypass",
    "no_authority_expansion",
    "no_further_provider_expansion",
)

FORBIDDEN_PROOF_ACTIONS: Final[tuple[tuple[str, str], ...]] = (
    ("provider_authority", "Never grant provider authority from proof evidence."),
    ("trust_mutation", "Never mutate trust from multi-cloud proof."),
    ("governance_bypass", "Never bypass governance from proof collection."),
    ("authority_expansion", "Never expand authority from proof program."),
)

MAX_MULTI_CLOUD_OPERATIONAL_PROOF_CONTENT_LEN: Final[int] = 8000
MAX_PERSISTED_MULTI_CLOUD_OPERATIONAL_PROOF_RECORDS: Final[int] = 500

MATURITY_LEVELS: Final[tuple[str, ...]] = (
    "NOT_PROVEN",
    "PARTIALLY_PROVEN",
    "PROVEN",
    "MATURE",
)

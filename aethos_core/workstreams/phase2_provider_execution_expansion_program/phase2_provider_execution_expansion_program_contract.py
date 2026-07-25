# SPDX-License-Identifier: Apache-2.0
"""WORKSTREAM_D1 / FIX 341 — Phase 2 provider execution expansion contract."""

from __future__ import annotations

from typing import Any, Final

PHASE2_PROVIDER_EXECUTION_EXPANSION_PROGRAM_ID: Final[str] = "WORKSTREAM_D1"
PHASE2_PROVIDER_EXECUTION_EXPANSION_PROGRAM_FIX: Final[str] = "FIX 341"
PHASE2_PROVIDER_EXECUTION_EXPANSION_PROGRAM_SCHEMA_VERSION: Final[str] = (
    "workstream_phase2_provider_execution_expansion_program_v1"
)
PHASE2_PROVIDER_EXECUTION_EXPANSION_PROGRAM_RECORD_SCHEMA_VERSION: Final[str] = (
    "workstream_phase2_provider_execution_expansion_program_record_v1"
)

CORE_PRINCIPLE: Final[str] = (
    "provider_expansion_inherits_existing_governance_without_authority_expansion"
)

MUTATION_PERFORMED_FIX_341: Final[bool] = False
EXECUTION_PERFORMED_FIX_341: Final[bool] = False
AUTHORITY_EXPANSION_FIX_341: Final[bool] = False
TRUST_MUTATION_AUTHORITY_FIX_341: Final[bool] = False
GOVERNANCE_BYPASS_AUTHORITY_FIX_341: Final[bool] = False
SPECIAL_PROVIDER_AUTHORITY_FIX_341: Final[bool] = False
ROLLBACK_EXECUTION_AUTHORITY_FIX_341: Final[bool] = False
GOVERNANCE_MUTATION_PERFORMED_FIX_341: Final[bool] = False
LOCAL_PHASE2_EXECUTION_EXECUTABLE_FIX_341: Final[bool] = True

PHASE2_PROVIDER_EXECUTION_EXPANSION_PROGRAM_ROUTE_ID: Final[str] = (
    "workstream_phase2_provider_execution_expansion_program"
)

PHASE2_PROVIDER_EXECUTION_EXPANSION_PROGRAM_INVARIANT: Final[str] = (
    "phase2_provider_execution_expansion_without_authority_expansion"
)

WAVE_1_PROVIDER_ORDER: Final[tuple[str, ...]] = ("AWS", "Kubernetes", "Azure", "GCP")

PHASE2_PROVIDER_EXECUTION_EXPANSION_PHASES: Final[tuple[str, ...]] = (
    "phase_1_provider_expansion_registry",
    "phase_2_aws_execution",
    "phase_3_kubernetes_execution",
    "phase_4_azure_execution",
    "phase_5_gcp_execution",
    "phase_6_verification_registry",
    "phase_7_readiness_assessment",
    "phase_8_expansion_dashboard",
    "phase_9_human_review",
)

PROVIDER_SCOPES: Final[dict[str, dict[str, Any]]] = {
    "AWS": {
        "display_name": "Amazon Web Services",
        "services": ("ECS", "Lambda", "API Gateway"),
        "deployment_report": "aws_deployment_report",
        "verification_report": "aws_verification_report",
        "evidence_bundle": "aws_evidence_bundle",
    },
    "Kubernetes": {
        "display_name": "Kubernetes",
        "services": ("deployment_rollout", "health_verification", "rollback_preparation"),
        "deployment_report": "kubernetes_deployment_report",
        "verification_report": "kubernetes_verification_report",
        "evidence_bundle": None,
    },
    "Azure": {
        "display_name": "Microsoft Azure",
        "services": ("App Service", "Container Apps"),
        "deployment_report": "azure_deployment_report",
        "verification_report": None,
        "evidence_bundle": None,
    },
    "GCP": {
        "display_name": "Google Cloud Platform",
        "services": ("Cloud Run", "Functions"),
        "deployment_report": "gcp_deployment_report",
        "verification_report": None,
        "evidence_bundle": None,
    },
}

HUMAN_PHASE2_EXPANSION_DECISION_KINDS: Final[tuple[str, ...]] = (
    "phase2_provider_expansion_review_approve",
    "phase2_provider_expansion_review_hold",
    "phase2_provider_expansion_review_reject",
    "phase2_provider_expansion_review_defer",
)

PHASE2_PROVIDER_EXECUTION_EXPANSION_RECORD_KINDS: Final[tuple[str, ...]] = (
    "phase2_provider_expansion_note",
    "phase2_provider_readiness_review_note",
    "phase2_provider_execution_review_note",
    *HUMAN_PHASE2_EXPANSION_DECISION_KINDS,
    "phase2_provider_deployed_note",
    "phase2_provider_execution_expansion_record",
)

PROGRAM_NON_GOALS: Final[tuple[str, ...]] = (
    "no_authority_expansion",
    "no_trust_mutation",
    "no_governance_bypass",
    "no_special_provider_authority",
    "no_rollback_execution",
)

FORBIDDEN_EXPANSION_ACTIONS: Final[tuple[tuple[str, str], ...]] = (
    ("authority_expansion", "Never expand authority for Phase 2 providers."),
    ("trust_mutation", "Never mutate trust from provider expansion."),
    ("governance_bypass", "Never bypass ET1–ET4 governance gates."),
    ("rollback_execution", "Rollback preparation only — no rollback execution."),
    ("special_provider_authority", "No provider receives special authority."),
)

MAX_PHASE2_PROVIDER_EXPANSION_CONTENT_LEN: Final[int] = 8000
MAX_PERSISTED_PHASE2_PROVIDER_EXPANSION_RECORDS: Final[int] = 500

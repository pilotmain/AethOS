# SPDX-License-Identifier: Apache-2.0
"""FIX 191 — cross-repository multi-agent delivery validation contract."""

from __future__ import annotations

from typing import Final

from aethos_core.mission_control.independent_repository_trust_expansion.independent_repository_trust_expansion_contract import (
    ALL_REGISTRY_REPOSITORIES,
    PHASE_1_REPOSITORY,
    PHASE_2_REPOSITORY_ORDER,
)

CROSS_REPOSITORY_MULTI_AGENT_DELIVERY_VALIDATION_SCHEMA_VERSION: Final[str] = (
    "mission_control_cross_repository_multi_agent_delivery_validation_v1"
)
CROSS_REPOSITORY_MULTI_AGENT_DELIVERY_VALIDATION_RECORD_SCHEMA_VERSION: Final[str] = (
    "mission_control_cross_repository_multi_agent_delivery_validation_record_v1"
)
CROSS_REPOSITORY_MULTI_AGENT_DELIVERY_VALIDATION_FIX: Final[str] = "FIX 191"

MUTATION_PERFORMED_FIX_191: Final[bool] = False
EXECUTION_PERFORMED_FIX_191: Final[bool] = False
PILOT_REEXECUTION_PERFORMED_FIX_191: Final[bool] = False
CROSS_REPO_VALIDATION_GRANTS_TRUST_FIX_191: Final[bool] = False
TRUST_TRANSFER_ENABLED_FIX_191: Final[bool] = False
MERGE_AUTHORITY_FIX_191: Final[bool] = False
DEPLOY_AUTHORITY_FIX_191: Final[bool] = False
RAILWAY_AUTHORITY_FIX_191: Final[bool] = False
PROVIDER_AUTHORITY_FIX_191: Final[bool] = False
GATE_BYPASS_ENABLED_FIX_191: Final[bool] = False
GOVERNANCE_MUTATION_PERFORMED_FIX_191: Final[bool] = False
VALIDATION_COMPOSES_ARTIFACTS_ONLY_FIX_191: Final[bool] = True

CROSS_REPOSITORY_MULTI_AGENT_DELIVERY_VALIDATION_ROUTE_ID: Final[str] = (
    "mission_control_cross_repository_multi_agent_delivery_validation"
)
CROSS_REPOSITORY_MULTI_AGENT_DELIVERY_VALIDATION_ORIGIN: Final[str] = (
    "mission_control_cross_repository_multi_agent_delivery_validation"
)

CROSS_REPOSITORY_MULTI_AGENT_DELIVERY_VALIDATION_INVARIANT: Final[str] = (
    "cross_repository_multi_agent_delivery_validation_composes_fix_188_189_190_artifacts_without_trust_granting_or_pilot_reexecution"
)

VALIDATION_TRUST_STATES: Final[tuple[str, ...]] = (
    "UNPROVEN",
    "PILOTING",
    "TRUST_REVIEW_PENDING",
    "CONDITIONALLY_TRUSTED",
)

PILOT_VALIDATION_MILESTONES: Final[tuple[str, ...]] = (
    "pilot_1",
    "pilot_2",
    "pilot_3",
    "trust_review",
)

REPOSITORY_PILOT_SESSIONS: Final[dict[str, tuple[str, ...]]] = {
    PHASE_1_REPOSITORY: ("dogfood-pilot-1", "dogfood-pilot-2", "dogfood-pilot-3"),
    PHASE_2_REPOSITORY_ORDER[0]: ("pilotos-pilot-1", "pilotos-pilot-2", "pilotos-pilot-3"),
    PHASE_2_REPOSITORY_ORDER[1]: ("atlas-pilot-1", "atlas-pilot-2", "atlas-pilot-3"),
    PHASE_2_REPOSITORY_ORDER[2]: ("nexora-pilot-1", "nexora-pilot-2", "nexora-pilot-3"),
}

REPOSITORY_DISPLAY_NAMES: Final[dict[str, str]] = {
    PHASE_1_REPOSITORY: "AethOS",
    PHASE_2_REPOSITORY_ORDER[0]: "PilotOS UI",
    PHASE_2_REPOSITORY_ORDER[1]: "Atlas Trader",
    PHASE_2_REPOSITORY_ORDER[2]: "Nexora",
}

VALIDATION_REPOSITORIES: Final[tuple[str, ...]] = ALL_REGISTRY_REPOSITORIES

CROSS_REPOSITORY_MULTI_AGENT_DELIVERY_VALIDATION_RECORD_KINDS: Final[tuple[str, ...]] = (
    "validation_observation",
    "cross_repo_evidence_note",
    "validation_annotation",
    "delivery_generalization_note",
    "cross_repository_multi_agent_delivery_validation_record",
)

CROSS_REPOSITORY_MULTI_AGENT_DELIVERY_VALIDATION_PRINCIPLES: Final[tuple[tuple[str, str], ...]] = (
    ("validation_not_trust", "Cross-repo validation ≠ trust granting."),
    ("compose_without_rerun", "Validation composes stored audits and receipts — never reruns pilots."),
    ("fix_188_pilot_arc", "Pilot arc evidence from FIX 188 where configured."),
    ("fix_189_agent_execution", "Agent execution evidence from FIX 189 receipts."),
    ("fix_190_agent_metrics", "Agent quality and throughput from FIX 190 metrics."),
    ("independent_repo_evidence", "Each repository validated independently — no inherited trust."),
    ("generalization_before_deploy", "Delivery generalization must be proven before merge/deploy lifecycle."),
    ("human_trust_decisions", "Humans still grant trust after validation review."),
)

FORBIDDEN_VALIDATION_ACTIONS: Final[tuple[tuple[str, str], ...]] = (
    ("trust_granting", "Validation never grants repository trust."),
    ("trust_transfer", "Validation never transfers trust between repositories."),
    ("pilot_reexecution", "Validation never reruns pilot harness."),
    ("agent_execution", "Validation never triggers agent execution."),
    ("merge", "Validation never merges pull requests."),
    ("deploy", "Validation never deploys."),
    ("railway_mutation", "Validation never mutates Railway."),
    ("provider_mutation", "Validation never mutates providers."),
    ("gate_bypass", "Validation never bypasses frozen gates."),
)

CROSS_REPOSITORY_MULTI_AGENT_DELIVERY_VALIDATION_EXECUTABLE: Final[bool] = False

MAX_CROSS_REPOSITORY_MULTI_AGENT_DELIVERY_VALIDATION_CONTENT_LEN: Final[int] = 4000
MAX_PERSISTED_CROSS_REPOSITORY_MULTI_AGENT_DELIVERY_VALIDATION_RECORDS: Final[int] = 500

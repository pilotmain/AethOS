# SPDX-License-Identifier: Apache-2.0
"""WORKSTREAM_E3 / FIX 345 — intelligence scalability implementation contract."""

from __future__ import annotations

from typing import Final

from aethos_core.workstreams.intelligence_runtime_optimization_program.intelligence_runtime_optimization_program_contract import (
    BASELINE_COMPOSE_TIMINGS_SEC,
    HIGH_VALUE_MEMOIZATION_MODULES,
    RECURSIVE_COMPOSE_CHAIN,
)

INTELLIGENCE_SCALABILITY_IMPLEMENTATION_PROGRAM_ID: Final[str] = "WORKSTREAM_E3"
INTELLIGENCE_SCALABILITY_IMPLEMENTATION_PROGRAM_FIX: Final[str] = "FIX 345"
INTELLIGENCE_SCALABILITY_IMPLEMENTATION_PROGRAM_SCHEMA_VERSION: Final[str] = (
    "workstream_intelligence_scalability_implementation_program_v1"
)
INTELLIGENCE_SCALABILITY_IMPLEMENTATION_PROGRAM_RECORD_SCHEMA_VERSION: Final[str] = (
    "workstream_intelligence_scalability_implementation_program_record_v1"
)

CORE_PRINCIPLE: Final[str] = (
    "optimization_execution_preserves_evidence_trust_and_governance_without_truth_mutation"
)

MUTATION_PERFORMED_FIX_345: Final[bool] = False
EXECUTION_PERFORMED_FIX_345: Final[bool] = True
TRUTH_MUTATION_FIX_345: Final[bool] = False
TRUST_MUTATION_AUTHORITY_FIX_345: Final[bool] = False
AUTHORITY_EXPANSION_FIX_345: Final[bool] = False
GOVERNANCE_BYPASS_AUTHORITY_FIX_345: Final[bool] = False
GOVERNANCE_MUTATION_PERFORMED_FIX_345: Final[bool] = False
LOCAL_SCALABILITY_IMPLEMENTATION_EXECUTABLE_FIX_345: Final[bool] = True

INTELLIGENCE_SCALABILITY_IMPLEMENTATION_PROGRAM_ROUTE_ID: Final[str] = (
    "workstream_intelligence_scalability_implementation_program"
)

INTELLIGENCE_SCALABILITY_IMPLEMENTATION_PROGRAM_INVARIANT: Final[str] = (
    "intelligence_scalability_implementation_without_truth_mutation_or_governance_change"
)

INTELLIGENCE_SCALABILITY_IMPLEMENTATION_PHASES: Final[tuple[str, ...]] = (
    "phase_1_memoization_implementation",
    "phase_2_pmf_snapshot_persistence",
    "phase_3_value_realization_snapshot_persistence",
    "phase_4_dependency_flattening_execution",
    "phase_5_runtime_benchmarking",
    "phase_6_truth_preservation_validation",
    "phase_7_scalability_opportunity_registry",
    "phase_8_executive_visibility",
    "phase_9_human_review",
)

EXECUTIVE_FIX_MODULES: Final[tuple[str, ...]] = (
    "FIX 316",
    "FIX 324",
    "FIX 329",
    "FIX 330",
)

MEMOIZATION_MODULES: Final[tuple[str, ...]] = HIGH_VALUE_MEMOIZATION_MODULES
PMF_SNAPSHOT_MODULE: Final[str] = "FIX 322"
VALUE_SNAPSHOT_MODULE: Final[str] = "FIX 323"

SCALABILITY_METRICS: Final[tuple[str, ...]] = (
    "compose_duration_reduction_pct",
    "cache_hit_ratio",
    "snapshot_reuse_ratio",
    "dependency_depth_reduction",
    "runtime_cost_reduction_pct",
)

HUMAN_SCALABILITY_DECISION_KINDS: Final[tuple[str, ...]] = (
    "scalability_review_approve",
    "scalability_review_hold",
    "scalability_review_reject",
    "scalability_review_defer",
)

INTELLIGENCE_SCALABILITY_RECORD_KINDS: Final[tuple[str, ...]] = (
    "scalability_note",
    *HUMAN_SCALABILITY_DECISION_KINDS,
    "scalability_implementation_note",
    "intelligence_scalability_implementation_program_record",
)

PROGRAM_NON_GOALS: Final[tuple[str, ...]] = (
    "no_new_intelligence_domains",
    "no_authority_expansion",
    "no_trust_mutation",
    "no_governance_changes",
    "no_provider_expansion",
)

FORBIDDEN_SCALABILITY_ACTIONS: Final[tuple[tuple[str, str], ...]] = (
    ("truth_mutation", "Never mutate truth from scalability implementation."),
    ("evidence_alteration", "Never alter authoritative evidence for performance."),
    ("trust_mutation", "Never mutate trust from runtime improvements."),
    ("governance_bypass", "Never bypass governance from scalability layer."),
    ("authority_expansion", "Never expand authority from scalability implementation."),
)

MAX_INTELLIGENCE_SCALABILITY_CONTENT_LEN: Final[int] = 8000
MAX_PERSISTED_INTELLIGENCE_SCALABILITY_RECORDS: Final[int] = 500

RUNTIME_BASELINE_COMPOSE_TIMINGS_SEC = BASELINE_COMPOSE_TIMINGS_SEC
RUNTIME_RECURSIVE_COMPOSE_CHAIN = RECURSIVE_COMPOSE_CHAIN

# SPDX-License-Identifier: Apache-2.0
"""WORKSTREAM_E2 / FIX 344 — intelligence runtime optimization program contract."""

from __future__ import annotations

from typing import Final

from aethos_core.workstreams.intelligence_performance_evidence_scalability_program.intelligence_performance_evidence_scalability_program_contract import (
    BASELINE_COMPOSE_TIMINGS_SEC,
    INTELLIGENCE_COMPOSE_DEPENDENCIES,
)

INTELLIGENCE_RUNTIME_OPTIMIZATION_PROGRAM_ID: Final[str] = "WORKSTREAM_E2"
INTELLIGENCE_RUNTIME_OPTIMIZATION_PROGRAM_FIX: Final[str] = "FIX 344"
INTELLIGENCE_RUNTIME_OPTIMIZATION_PROGRAM_SCHEMA_VERSION: Final[str] = (
    "workstream_intelligence_runtime_optimization_program_v1"
)
INTELLIGENCE_RUNTIME_OPTIMIZATION_PROGRAM_RECORD_SCHEMA_VERSION: Final[str] = (
    "workstream_intelligence_runtime_optimization_program_record_v1"
)

CORE_PRINCIPLE: Final[str] = (
    "runtime_optimization_preserves_evidence_trust_and_governance_without_truth_reduction"
)

MUTATION_PERFORMED_FIX_344: Final[bool] = False
EXECUTION_PERFORMED_FIX_344: Final[bool] = False
TRUTH_REDUCTION_FIX_344: Final[bool] = False
TRUST_MUTATION_AUTHORITY_FIX_344: Final[bool] = False
AUTHORITY_EXPANSION_FIX_344: Final[bool] = False
GOVERNANCE_BYPASS_AUTHORITY_FIX_344: Final[bool] = False
GOVERNANCE_MUTATION_PERFORMED_FIX_344: Final[bool] = False
LOCAL_RUNTIME_OPTIMIZATION_EXECUTABLE_FIX_344: Final[bool] = True

INTELLIGENCE_RUNTIME_OPTIMIZATION_PROGRAM_ROUTE_ID: Final[str] = (
    "workstream_intelligence_runtime_optimization_program"
)

INTELLIGENCE_RUNTIME_OPTIMIZATION_PROGRAM_INVARIANT: Final[str] = (
    "intelligence_runtime_optimization_without_truth_reduction_trust_or_governance_change"
)

INTELLIGENCE_RUNTIME_OPTIMIZATION_PHASES: Final[tuple[str, ...]] = (
    "phase_1_runtime_dependency_registry",
    "phase_2_memoization_opportunity_analysis",
    "phase_3_artifact_persistence_analysis",
    "phase_4_dependency_flattening_analysis",
    "phase_5_runtime_hotspot_registry",
    "phase_6_optimization_opportunity_registry",
    "phase_7_optimization_priority_matrix",
    "phase_8_executive_visibility",
    "phase_9_human_review",
)

EXECUTIVE_FIX_MODULES: Final[tuple[str, ...]] = (
    "FIX 316",
    "FIX 324",
    "FIX 329",
    "FIX 330",
)

HIGH_VALUE_MEMOIZATION_MODULES: Final[tuple[str, ...]] = ("FIX 295", "FIX 296", "FIX 301")

ARTIFACT_PERSISTENCE_CANDIDATES: Final[tuple[str, ...]] = (
    "FIX 322",
    "FIX 323",
    "FIX 320",
    "FIX 321",
)

RECURSIVE_COMPOSE_CHAIN: Final[tuple[str, ...]] = (
    "FIX 323",
    "FIX 322",
    "FIX 320",
    "FIX 319",
    "FIX 318",
)

FLATTENING_TARGET: Final[tuple[str, ...]] = ("FIX 323", "FIX 322 Snapshot")

RUNTIME_OPTIMIZATION_METRICS: Final[tuple[str, ...]] = (
    "compose_duration_reduction",
    "cache_hit_ratio",
    "artifact_reuse_ratio",
    "dependency_depth_reduction",
    "recomposition_reduction",
)

HUMAN_RUNTIME_OPTIMIZATION_DECISION_KINDS: Final[tuple[str, ...]] = (
    "runtime_optimization_review_approve",
    "runtime_optimization_review_hold",
    "runtime_optimization_review_reject",
    "runtime_optimization_review_defer",
)

INTELLIGENCE_RUNTIME_OPTIMIZATION_RECORD_KINDS: Final[tuple[str, ...]] = (
    "runtime_optimization_note",
    *HUMAN_RUNTIME_OPTIMIZATION_DECISION_KINDS,
    "runtime_optimization_probe_note",
    "intelligence_runtime_optimization_program_record",
)

PROGRAM_NON_GOALS: Final[tuple[str, ...]] = (
    "no_authority_expansion",
    "no_governance_bypass",
    "no_trust_mutation",
    "no_evidence_deletion",
    "no_answer_quality_reduction",
    "no_provider_execution_changes",
)

FORBIDDEN_RUNTIME_OPTIMIZATION_ACTIONS: Final[tuple[tuple[str, str], ...]] = (
    ("truth_reduction", "Never reduce evidence quality for runtime gains."),
    ("evidence_deletion", "Never delete authoritative evidence for speed."),
    ("trust_mutation", "Never mutate trust from runtime optimization."),
    ("governance_bypass", "Never bypass governance from runtime layer."),
    ("authority_expansion", "Never expand authority from runtime optimization."),
)

MAX_INTELLIGENCE_RUNTIME_OPTIMIZATION_CONTENT_LEN: Final[int] = 8000
MAX_PERSISTED_INTELLIGENCE_RUNTIME_OPTIMIZATION_RECORDS: Final[int] = 500

# Re-export shared compose graph for E2 analysis.
RUNTIME_COMPOSE_DEPENDENCIES = INTELLIGENCE_COMPOSE_DEPENDENCIES
RUNTIME_BASELINE_COMPOSE_TIMINGS_SEC = BASELINE_COMPOSE_TIMINGS_SEC

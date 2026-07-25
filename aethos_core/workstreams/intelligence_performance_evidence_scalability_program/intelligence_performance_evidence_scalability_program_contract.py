# SPDX-License-Identifier: Apache-2.0
"""WORKSTREAM_E1 / FIX 343 — intelligence performance & evidence scalability contract."""

from __future__ import annotations

from typing import Any, Final

INTELLIGENCE_PERFORMANCE_EVIDENCE_SCALABILITY_PROGRAM_ID: Final[str] = "WORKSTREAM_E1"
INTELLIGENCE_PERFORMANCE_EVIDENCE_SCALABILITY_PROGRAM_FIX: Final[str] = "FIX 343"
INTELLIGENCE_PERFORMANCE_EVIDENCE_SCALABILITY_PROGRAM_SCHEMA_VERSION: Final[str] = (
    "workstream_intelligence_performance_evidence_scalability_program_v1"
)
INTELLIGENCE_PERFORMANCE_EVIDENCE_SCALABILITY_PROGRAM_RECORD_SCHEMA_VERSION: Final[str] = (
    "workstream_intelligence_performance_evidence_scalability_program_record_v1"
)

CORE_PRINCIPLE: Final[str] = (
    "performance_optimization_preserves_evidence_integrity_without_truth_reduction"
)

MUTATION_PERFORMED_FIX_343: Final[bool] = False
EXECUTION_PERFORMED_FIX_343: Final[bool] = False
TRUTH_REDUCTION_FIX_343: Final[bool] = False
TRUST_MUTATION_AUTHORITY_FIX_343: Final[bool] = False
AUTHORITY_EXPANSION_FIX_343: Final[bool] = False
GOVERNANCE_BYPASS_AUTHORITY_FIX_343: Final[bool] = False
GOVERNANCE_MUTATION_PERFORMED_FIX_343: Final[bool] = False
LOCAL_PERFORMANCE_ANALYSIS_EXECUTABLE_FIX_343: Final[bool] = True

INTELLIGENCE_PERFORMANCE_EVIDENCE_SCALABILITY_PROGRAM_ROUTE_ID: Final[str] = (
    "workstream_intelligence_performance_evidence_scalability_program"
)

INTELLIGENCE_PERFORMANCE_EVIDENCE_SCALABILITY_PROGRAM_INVARIANT: Final[str] = (
    "intelligence_performance_optimization_without_truth_reduction_or_governance_change"
)

INTELLIGENCE_PERFORMANCE_PHASES: Final[tuple[str, ...]] = (
    "phase_1_compose_timing_registry",
    "phase_2_dependency_analysis",
    "phase_3_evidence_caching_analysis",
    "phase_4_incremental_composition",
    "phase_5_hotspot_registry",
    "phase_6_optimization_opportunities",
    "phase_7_performance_priority_matrix",
    "phase_8_executive_visibility",
    "phase_9_human_review",
)

EXECUTIVE_FIX_MODULES: Final[tuple[str, ...]] = (
    "FIX 316",
    "FIX 324",
    "FIX 329",
    "FIX 330",
)

# Measured compose durations (seconds) from WORKSTREAM_B1 baseline probe.
BASELINE_COMPOSE_TIMINGS_SEC: Final[dict[str, float]] = {
    "FIX 295": 0.01,
    "FIX 296": 0.03,
    "FIX 301": 0.054,
    "FIX 314": 179.986,
    "FIX 319": 287.919,
    "FIX 323": 2751.482,
    "FIX 322": 5070.368,
}

# Static dependency fan-out from Mission Control evidence collectors.
INTELLIGENCE_COMPOSE_DEPENDENCIES: Final[dict[str, tuple[str, ...]]] = {
    "FIX 295": (),
    "FIX 296": (),
    "FIX 301": (),
    "FIX 310": (),
    "FIX 314": ("FIX 301", "FIX 295", "FIX 296", "FIX 319"),
    "FIX 318": ("FIX 295", "FIX 296"),
    "FIX 319": (
        "FIX 295",
        "FIX 296",
        "FIX 301",
        "FIX 303",
        "FIX 310",
        "FIX 311",
        "FIX 312",
        "FIX 317",
        "FIX 318",
    ),
    "FIX 320": ("FIX 295", "FIX 296", "FIX 318", "FIX 319"),
    "FIX 321": ("FIX 295", "FIX 296", "FIX 318", "FIX 319", "FIX 320"),
    "FIX 322": ("FIX 295", "FIX 296", "FIX 318", "FIX 319", "FIX 320", "FIX 321"),
    "FIX 323": (
        "FIX 295",
        "FIX 301",
        "FIX 310",
        "FIX 318",
        "FIX 320",
        "FIX 321",
        "FIX 322",
    ),
}

EVIDENCE_VOLATILITY_CLASSES: Final[tuple[str, ...]] = (
    "static_evidence",
    "slow_changing_evidence",
    "dynamic_evidence",
)

HUMAN_PERFORMANCE_DECISION_KINDS: Final[tuple[str, ...]] = (
    "performance_review_approve",
    "performance_review_hold",
    "performance_review_reject",
    "performance_review_defer",
)

INTELLIGENCE_PERFORMANCE_RECORD_KINDS: Final[tuple[str, ...]] = (
    "performance_note",
    *HUMAN_PERFORMANCE_DECISION_KINDS,
    "performance_analysis_note",
    "intelligence_performance_program_record",
)

PROGRAM_NON_GOALS: Final[tuple[str, ...]] = (
    "no_truth_reduction",
    "no_trust_mutation",
    "no_governance_bypass",
    "no_authority_expansion",
    "no_evidence_quality_degradation",
)

FORBIDDEN_PERFORMANCE_ACTIONS: Final[tuple[tuple[str, str], ...]] = (
    ("truth_reduction", "Never reduce evidence quality for performance gains."),
    ("trust_mutation", "Never mutate trust from performance optimization."),
    ("governance_bypass", "Never bypass governance from performance layer."),
    ("authority_expansion", "Never expand authority from performance optimization."),
    ("evidence_deletion", "Never delete authoritative evidence for speed."),
)

MAX_INTELLIGENCE_PERFORMANCE_CONTENT_LEN: Final[int] = 8000
MAX_PERSISTED_INTELLIGENCE_PERFORMANCE_RECORDS: Final[int] = 500

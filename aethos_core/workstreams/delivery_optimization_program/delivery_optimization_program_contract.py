# SPDX-License-Identifier: Apache-2.0
"""WORKSTREAM_C2 / FIX 340 — delivery optimization program contract."""

from __future__ import annotations

from typing import Final

DELIVERY_OPTIMIZATION_PROGRAM_ID: Final[str] = "WORKSTREAM_C2"
DELIVERY_OPTIMIZATION_PROGRAM_FIX: Final[str] = "FIX 340"
DELIVERY_OPTIMIZATION_PROGRAM_SCHEMA_VERSION: Final[str] = (
    "workstream_delivery_optimization_program_v1"
)
DELIVERY_OPTIMIZATION_PROGRAM_RECORD_SCHEMA_VERSION: Final[str] = (
    "workstream_delivery_optimization_program_record_v1"
)

CORE_PRINCIPLE: Final[str] = (
    "delivery_optimization_recommends_improvements_humans_decide_adoption_without_autonomous_mutation"
)

MUTATION_PERFORMED_FIX_340: Final[bool] = False
EXECUTION_PERFORMED_FIX_340: Final[bool] = False
AUTONOMOUS_MUTATION_ENABLED_FIX_340: Final[bool] = False
DELIVERY_AUTHORITY_FIX_340: Final[bool] = False
TRUST_MUTATION_AUTHORITY_FIX_340: Final[bool] = False
AUTHORITY_EXPANSION_FIX_340: Final[bool] = False
GOVERNANCE_BYPASS_AUTHORITY_FIX_340: Final[bool] = False
PROVIDER_MUTATION_AUTHORITY_FIX_340: Final[bool] = False
GOVERNANCE_MUTATION_PERFORMED_FIX_340: Final[bool] = False
LOCAL_OPTIMIZATION_ANALYSIS_EXECUTABLE_FIX_340: Final[bool] = True

DELIVERY_OPTIMIZATION_PROGRAM_ROUTE_ID: Final[str] = "workstream_delivery_optimization_program"

DELIVERY_OPTIMIZATION_PROGRAM_INVARIANT: Final[str] = (
    "delivery_optimization_without_autonomous_mutation_or_authority_expansion"
)

DELIVERY_OPTIMIZATION_PHASES: Final[tuple[str, ...]] = (
    "phase_1_delivery_outcome_registry",
    "phase_2_failure_intelligence",
    "phase_3_intervention_intelligence",
    "phase_4_performance_intelligence",
    "phase_5_reliability_intelligence",
    "phase_6_improvement_opportunity_registry",
    "phase_7_optimization_priority_matrix",
    "phase_8_executive_visibility",
    "phase_9_human_review",
)

EXECUTION_TRACK_FAILURE_KEYS: Final[tuple[str, ...]] = (
    "execution_track_1",
    "execution_track_2",
    "execution_track_3",
    "execution_track_4",
    "execution_track_5",
)

IMPROVEMENT_CATEGORIES: Final[tuple[str, ...]] = (
    "process_improvement",
    "tooling_improvement",
    "workflow_improvement",
    "provider_improvement",
)

OPTIMIZATION_TREND_METRICS: Final[tuple[str, ...]] = (
    "deployment_success_trend",
    "intervention_reduction_trend",
    "delivery_cycle_time_trend",
    "recovery_trend",
    "verification_trend",
)

EXECUTIVE_FIX_MODULES: Final[tuple[str, ...]] = (
    "FIX 316",
    "FIX 324",
    "FIX 329",
    "FIX 330",
)

HUMAN_OPTIMIZATION_DECISION_KINDS: Final[tuple[str, ...]] = (
    "delivery_optimization_review_approve",
    "delivery_optimization_review_hold",
    "delivery_optimization_review_reject",
    "delivery_optimization_review_defer",
)

DELIVERY_OPTIMIZATION_RECORD_KINDS: Final[tuple[str, ...]] = (
    "delivery_optimization_note",
    *HUMAN_OPTIMIZATION_DECISION_KINDS,
    "delivery_optimization_analysis_note",
    "delivery_optimization_program_record",
)

PROGRAM_NON_GOALS: Final[tuple[str, ...]] = (
    "no_automatic_self_modification",
    "no_authority_expansion",
    "no_trust_mutation",
    "no_governance_bypass",
    "no_provider_mutation",
)

FORBIDDEN_OPTIMIZATION_ACTIONS: Final[tuple[tuple[str, str], ...]] = (
    ("autonomous_mutation", "Never modify the delivery engine automatically."),
    ("authority_expansion", "Never expand delivery authority from optimization."),
    ("trust_mutation", "Never mutate trust from optimization recommendations."),
    ("governance_bypass", "Never bypass governance from optimization layer."),
    ("provider_mutation", "Never mutate providers from optimization layer."),
)

MAX_DELIVERY_OPTIMIZATION_CONTENT_LEN: Final[int] = 8000
MAX_PERSISTED_DELIVERY_OPTIMIZATION_RECORDS: Final[int] = 500

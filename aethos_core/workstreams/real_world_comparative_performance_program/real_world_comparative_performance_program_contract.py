# SPDX-License-Identifier: Apache-2.0
"""PHASE_J2 / FIX 365 — real-world comparative performance program contract."""

from __future__ import annotations

from typing import Final

REAL_WORLD_COMPARATIVE_PERFORMANCE_PROGRAM_ID: Final[str] = "PHASE_J2"
REAL_WORLD_COMPARATIVE_PERFORMANCE_PROGRAM_FIX: Final[str] = "FIX 365"
REAL_WORLD_COMPARATIVE_PERFORMANCE_PROGRAM_SCHEMA_VERSION: Final[str] = (
    "phase_real_world_comparative_performance_program_v1"
)
REAL_WORLD_COMPARATIVE_PERFORMANCE_PROGRAM_RECORD_SCHEMA_VERSION: Final[str] = (
    "phase_real_world_comparative_performance_program_record_v1"
)

CORE_PRINCIPLE: Final[str] = (
    "comparative_performance_evaluates_outcomes_without_competitive_authority"
)

MUTATION_PERFORMED_FIX_365: Final[bool] = False
GOVERNANCE_MUTATION_PERFORMED_FIX_365: Final[bool] = False
COMPETITIVE_AUTHORITY_FIX_365: Final[bool] = False
COMPETITIVE_ACTIONS_FIX_365: Final[bool] = False
STRATEGY_MUTATION_FIX_365: Final[bool] = False
AUTHORITY_EXPANSION_FIX_365: Final[bool] = False
GOVERNANCE_MUTATION_FIX_365: Final[bool] = False
GOVERNANCE_BYPASS_FIX_365: Final[bool] = False
TRUST_PROMOTION_FIX_365: Final[bool] = False
GOVERNANCE_BYPASS_AUTHORITY_FIX_365: Final[bool] = False
TRUST_MUTATION_AUTHORITY_FIX_365: Final[bool] = False
LOCAL_REAL_WORLD_COMPARATIVE_PERFORMANCE_EXECUTABLE_FIX_365: Final[bool] = True

REAL_WORLD_COMPARATIVE_PERFORMANCE_PROGRAM_ROUTE_ID: Final[str] = (
    "phase_real_world_comparative_performance_program"
)

REAL_WORLD_COMPARATIVE_PERFORMANCE_PROGRAM_INVARIANT: Final[str] = (
    "comparative_performance_without_competitive_authority_strategy_mutation_or_trust_promotion"
)

REAL_WORLD_COMPARATIVE_PERFORMANCE_PHASES: Final[tuple[str, ...]] = (
    "phase_1_benchmark_registry",
    "phase_2_delivery_comparison_analysis",
    "phase_3_deployment_comparison_analysis",
    "phase_4_customer_outcome_comparison",
    "phase_5_operational_comparison_analysis",
    "phase_6_comparative_learning_analysis",
    "phase_7_comparative_opportunity_registry",
    "phase_8_executive_visibility",
    "phase_9_human_review",
)

COMPARISON_LEVELS: Final[tuple[str, ...]] = (
    "unknown",
    "comparable",
    "advantage",
    "significant_advantage",
    "transformational",
)

BENCHMARK_APPROACHES: Final[tuple[str, ...]] = (
    "aethos",
    "human_only",
    "traditional_workflow",
    "assisted_workflow",
)

BENCHMARK_CATEGORIES: Final[tuple[str, ...]] = (
    "delivery",
    "deployment",
    "recovery",
    "customer",
    "operational",
)

COMPARATIVE_PERFORMANCE_METRICS: Final[tuple[str, ...]] = (
    "delivery_performance_delta",
    "deployment_performance_delta",
    "recovery_performance_delta",
    "customer_outcome_delta",
    "operational_efficiency_delta",
)

EXECUTIVE_WORKSTREAM_MODULES: Final[tuple[str, ...]] = (
    "PHASE_J1",
    "PHASE_I3",
    "WORKSTREAM_G4",
    "WORKSTREAM_H3",
    "FIX_330",
)

HUMAN_COMPARATIVE_PERFORMANCE_DECISION_KINDS: Final[tuple[str, ...]] = (
    "comparative_performance_review_approve",
    "comparative_performance_review_hold",
    "comparative_performance_review_reject",
    "comparative_performance_review_defer",
)

COMPARATIVE_PERFORMANCE_RECORD_KINDS: Final[tuple[str, ...]] = (
    "comparative_performance_note",
    "comparative_performance_benchmark_entry",
    *HUMAN_COMPARATIVE_PERFORMANCE_DECISION_KINDS,
    "comparative_performance_record",
)

BENCHMARK_MIN_SIZE: Final[int] = 1

PROGRAM_NON_GOALS: Final[tuple[str, ...]] = (
    "no_competitive_actions",
    "no_strategy_mutation",
    "no_authority_expansion",
    "no_governance_mutation",
    "no_trust_promotion",
)

FORBIDDEN_COMPARATIVE_PERFORMANCE_ACTIONS: Final[tuple[tuple[str, str], ...]] = (
    ("competitive_authority", "Never declare superiority or competitive authority from comparison."),
    ("competitive_actions", "Never automate competitive actions from comparative performance."),
    ("strategy_mutation", "Never modify strategy from comparative performance measurement."),
    ("authority_expansion", "Never expand authority from comparative performance."),
    ("governance_mutation", "Never change governance from comparative performance."),
    ("trust_promotion", "Never alter trust from comparative performance."),
)

MAX_COMPARATIVE_PERFORMANCE_CONTENT_LEN: Final[int] = 8000
MAX_PERSISTED_COMPARATIVE_PERFORMANCE_RECORDS: Final[int] = 500

# SPDX-License-Identifier: Apache-2.0
"""FIX 322 — product-market fit intelligence contract."""

from __future__ import annotations

from typing import Final

PRODUCT_MARKET_FIT_INTELLIGENCE_SCHEMA_VERSION: Final[str] = "mission_control_product_market_fit_intelligence_v1"
PRODUCT_MARKET_FIT_INTELLIGENCE_RECORD_SCHEMA_VERSION: Final[str] = (
    "mission_control_product_market_fit_intelligence_record_v1"
)
PRODUCT_MARKET_FIT_INTELLIGENCE_FIX: Final[str] = "FIX 322"

MUTATION_PERFORMED_FIX_322: Final[bool] = False
EXECUTION_PERFORMED_FIX_322: Final[bool] = False
PMF_AUTHORITY_FIX_322: Final[bool] = False
AUTOMATIC_PRODUCT_STRATEGY_ENABLED_FIX_322: Final[bool] = False
AUTOMATIC_FEATURE_CREATION_ENABLED_FIX_322: Final[bool] = False
AUTOMATIC_PRICING_CHANGES_ENABLED_FIX_322: Final[bool] = False
GOVERNANCE_MUTATION_PERFORMED_FIX_322: Final[bool] = False
PRODUCT_MARKET_FIT_COMPOSES_EVIDENCE_ONLY_FIX_322: Final[bool] = True

PRODUCT_MARKET_FIT_INTELLIGENCE_ROUTE_ID: Final[str] = "mission_control_product_market_fit_intelligence"

PRODUCT_MARKET_FIT_INTELLIGENCE_INVARIANT: Final[str] = (
    "product_market_fit_intelligence_without_product_strategy_authority"
)

PRODUCT_MARKET_FIT_INTELLIGENCE_DOMAINS: Final[tuple[str, ...]] = (
    "value_signal_registry",
    "problem_solution_fit_report",
    "customer_value_realization_report",
    "capability_demand_report",
    "retention_value_report",
    "expansion_value_report",
    "pmf_opportunity_registry",
    "pmf_scorecard",
    "product_market_fit_dashboard",
    "pmf_review_registry",
)

PMF_SCORECARD_DIMENSIONS: Final[tuple[str, ...]] = (
    "demand",
    "adoption",
    "retention",
    "expansion",
    "advocacy",
)

PMF_FIT_LEVELS: Final[tuple[str, ...]] = (
    "UNKNOWN",
    "EARLY_SIGNAL",
    "DEVELOPING",
    "STRONG",
    "ESTABLISHED",
)

PMF_CORE_PRINCIPLE: Final[str] = "product_market_fit_intelligence ≠ product_strategy_authority"

PRIVACY_REQUIREMENTS: Final[tuple[str, ...]] = (
    "no_cross_tenant_exposure",
    "no_customer_targeting",
    "no_customer_profiling",
    "no_automatic_growth_actions",
    "tenant_isolation_preserved",
)

HUMAN_PMF_REVIEW_DECISION_KINDS: Final[tuple[str, ...]] = (
    "pmf_review_decision_approve",
    "pmf_review_decision_hold",
    "pmf_review_decision_reject",
    "pmf_review_decision_defer",
)

PMF_REVIEW_RECORD_KINDS: Final[tuple[str, ...]] = (
    "pmf_note",
    *HUMAN_PMF_REVIEW_DECISION_KINDS,
    "pmf_snapshot",
)

FORBIDDEN_PMF_ACTIONS: Final[tuple[tuple[str, str], ...]] = (
    ("automatic_product_strategy", "Never sets product strategy automatically."),
    ("automatic_feature_creation", "Never creates features automatically from PMF signals."),
    ("automatic_pricing_changes", "Never changes pricing automatically."),
    ("cross_tenant_pmf_analysis", "Never aggregates PMF signals across tenants."),
)

PRODUCT_MARKET_FIT_INTELLIGENCE_EXECUTABLE: Final[bool] = False

MAX_PMF_REVIEW_CONTENT_LEN: Final[int] = 4000
MAX_PERSISTED_PMF_REVIEW_RECORDS: Final[int] = 500

# SPDX-License-Identifier: Apache-2.0
"""FIX 317 — continuous product improvement contract."""

from __future__ import annotations

from typing import Final

CONTINUOUS_PRODUCT_IMPROVEMENT_SCHEMA_VERSION: Final[str] = (
    "mission_control_continuous_product_improvement_v1"
)
CONTINUOUS_PRODUCT_IMPROVEMENT_RECORD_SCHEMA_VERSION: Final[str] = (
    "mission_control_continuous_product_improvement_record_v1"
)
CONTINUOUS_PRODUCT_IMPROVEMENT_FIX: Final[str] = "FIX 317"

MUTATION_PERFORMED_FIX_317: Final[bool] = False
EXECUTION_PERFORMED_FIX_317: Final[bool] = False
CONTINUOUS_IMPROVEMENT_AUTHORITY_FIX_317: Final[bool] = False
AUTOMATIC_BACKLOG_CREATION_ENABLED_FIX_317: Final[bool] = False
AUTOMATIC_FEATURE_CREATION_ENABLED_FIX_317: Final[bool] = False
AUTOMATIC_PRODUCT_MUTATION_ENABLED_FIX_317: Final[bool] = False
GOVERNANCE_MUTATION_PERFORMED_FIX_317: Final[bool] = False
CONTINUOUS_IMPROVEMENT_COMPOSES_EVIDENCE_ONLY_FIX_317: Final[bool] = True

CONTINUOUS_PRODUCT_IMPROVEMENT_ROUTE_ID: Final[str] = (
    "mission_control_continuous_product_improvement"
)

CONTINUOUS_PRODUCT_IMPROVEMENT_INVARIANT: Final[str] = (
    "continuous_product_improvement_without_automatic_execution"
)

CONTINUOUS_PRODUCT_IMPROVEMENT_DOMAINS: Final[tuple[str, ...]] = (
    "feedback_intelligence_report",
    "onboarding_improvement_report",
    "product_experience_improvement_report",
    "operational_improvement_report",
    "governance_improvement_report",
    "commercial_improvement_report",
    "improvement_opportunity_registry",
    "improvement_priority_matrix",
    "continuous_improvement_dashboard",
    "improvement_review_registry",
)

HUMAN_IMPROVEMENT_REVIEW_DECISION_KINDS: Final[tuple[str, ...]] = (
    "improvement_review_decision_approve",
    "improvement_review_decision_hold",
    "improvement_review_decision_reject",
    "improvement_review_decision_defer",
)

IMPROVEMENT_REVIEW_RECORD_KINDS: Final[tuple[str, ...]] = (
    "improvement_note",
    *HUMAN_IMPROVEMENT_REVIEW_DECISION_KINDS,
    "improvement_snapshot",
)

CONTINUOUS_PRODUCT_IMPROVEMENT_PRINCIPLES: Final[tuple[tuple[str, str], ...]] = (
    ("recommendations_not_execution", "improvement_recommendations ≠ automatic_execution"),
    ("humans_decide", "AethOS identifies opportunities; humans decide what to pursue."),
    ("compose_only", "Composes FIX 300–313 observations without creating work automatically."),
    ("no_backlog_mutation", "No automatic backlog, feature, project, or roadmap creation."),
)

FORBIDDEN_CONTINUOUS_IMPROVEMENT_ACTIONS: Final[tuple[tuple[str, str], ...]] = (
    ("automatic_feature_creation", "Never creates features automatically."),
    ("automatic_issue_creation", "Never creates issues automatically."),
    ("automatic_project_creation", "Never creates projects automatically."),
    ("automatic_roadmap_change", "Never changes roadmap automatically."),
    ("automatic_trust_mutation", "Never changes trust baselines automatically."),
)

CONTINUOUS_PRODUCT_IMPROVEMENT_EXECUTABLE: Final[bool] = False

MAX_IMPROVEMENT_REVIEW_CONTENT_LEN: Final[int] = 4000
MAX_PERSISTED_IMPROVEMENT_REVIEW_RECORDS: Final[int] = 500

IMPACT_LEVELS: Final[tuple[str, ...]] = ("high", "medium", "low")
EFFORT_LEVELS: Final[tuple[str, ...]] = ("low", "medium", "high")

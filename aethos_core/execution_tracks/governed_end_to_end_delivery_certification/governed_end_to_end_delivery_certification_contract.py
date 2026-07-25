# SPDX-License-Identifier: Apache-2.0
"""FIX 338 / EXECUTION_TRACK_5 — end-to-end delivery certification contract."""

from __future__ import annotations

from typing import Any, Final

EXECUTION_TRACK_5_ID: Final[str] = "EXECUTION_TRACK_5"
GOVERNED_END_TO_END_DELIVERY_CERTIFICATION_FIX: Final[str] = "FIX 338"
GOVERNED_END_TO_END_DELIVERY_CERTIFICATION_SCHEMA_VERSION: Final[str] = (
    "execution_track_governed_end_to_end_delivery_certification_v1"
)
GOVERNED_END_TO_END_DELIVERY_CERTIFICATION_RECORD_SCHEMA_VERSION: Final[str] = (
    "execution_track_governed_end_to_end_delivery_certification_record_v1"
)

CORE_PRINCIPLE: Final[str] = (
    "delivery_certification_measures_execution_quality_without_granting_delivery_authority"
)

MUTATION_PERFORMED_FIX_338: Final[bool] = False
EXECUTION_PERFORMED_FIX_338: Final[bool] = False
DELIVERY_AUTHORITY_FIX_338: Final[bool] = False
TRUST_MUTATION_AUTHORITY_FIX_338: Final[bool] = False
AUTOMATIC_CERTIFICATION_PROMOTION_FIX_338: Final[bool] = False
APPROVAL_BYPASS_AUTHORITY_FIX_338: Final[bool] = False
DEPLOYMENT_BYPASS_AUTHORITY_FIX_338: Final[bool] = False
AUTHORITY_ESCALATION_FIX_338: Final[bool] = False
GOVERNANCE_MUTATION_PERFORMED_FIX_338: Final[bool] = False
LOCAL_CERTIFICATION_EXECUTABLE_FIX_338: Final[bool] = True

GOVERNED_END_TO_END_DELIVERY_CERTIFICATION_ROUTE_ID: Final[str] = (
    "execution_track_governed_end_to_end_delivery_certification"
)

GOVERNED_END_TO_END_DELIVERY_CERTIFICATION_INVARIANT: Final[str] = (
    "governed_end_to_end_delivery_certification_without_delivery_or_trust_authority"
)

EXECUTION_TRACK_5_PHASES: Final[tuple[str, ...]] = (
    "phase_1_delivery_run_registry",
    "phase_2_execution_quality",
    "phase_3_reliability_analysis",
    "phase_4_failure_intelligence",
    "phase_5_human_intervention_analysis",
    "phase_6_evidence_certification",
    "phase_7_readiness_assessment",
    "phase_8_certification_dashboard",
    "phase_9_human_review",
)

CERTIFICATION_STATUSES: Final[tuple[str, ...]] = (
    "NOT_CERTIFIED",
    "PARTIALLY_CERTIFIED",
    "CERTIFIED",
    "PRODUCTION_CERTIFIED",
)

CERTIFICATION_SCENARIO_IDS: Final[tuple[str, ...]] = (
    "scenario_1_fastapi_railway",
    "scenario_2_spring_boot_railway",
    "scenario_3_nextjs_vercel",
    "scenario_4_bug_fix_delivery",
    "scenario_5_documentation_change",
)

CERTIFICATION_SCENARIOS: Final[dict[str, dict[str, Any]]] = {
    "scenario_1_fastapi_railway": {
        "name": "FastAPI service",
        "template_id": "fastapi_service",
        "workspace_name": "cert-fastapi-api",
        "provider": "railway",
        "environment": "staging",
        "generation_type": "story",
        "feature_name": "health-check-endpoint",
        "includes_workspace": True,
        "includes_deployment": True,
    },
    "scenario_2_spring_boot_railway": {
        "name": "Spring Boot service",
        "template_id": "spring_boot_service",
        "workspace_name": "cert-spring-api",
        "provider": "railway",
        "environment": "staging",
        "generation_type": "story",
        "feature_name": "actuator-health",
        "includes_workspace": True,
        "includes_deployment": True,
    },
    "scenario_3_nextjs_vercel": {
        "name": "Next.js application",
        "template_id": "nextjs_web_app",
        "workspace_name": "cert-nextjs-app",
        "provider": "vercel",
        "environment": "preview",
        "generation_type": "story",
        "feature_name": "landing-page",
        "includes_workspace": True,
        "includes_deployment": True,
    },
    "scenario_4_bug_fix_delivery": {
        "name": "Bug Fix Delivery",
        "template_id": "generic_repository",
        "workspace_name": "existing-repo",
        "provider": "railway",
        "environment": "staging",
        "generation_type": "bug",
        "feature_name": "null-pointer-fix",
        "includes_workspace": False,
        "existing_repository": True,
        "includes_deployment": True,
    },
    "scenario_5_documentation_change": {
        "name": "Documentation Change",
        "template_id": "generic_repository",
        "workspace_name": "docs-repo",
        "provider": "",
        "environment": "",
        "generation_type": "task",
        "feature_name": "readme-update",
        "includes_workspace": False,
        "includes_deployment": False,
        "documentation_only": True,
    },
}

HUMAN_CERTIFICATION_DECISION_KINDS: Final[tuple[str, ...]] = (
    "certification_decision_approve",
    "certification_decision_hold",
    "certification_decision_reject",
    "certification_decision_defer",
)

REQUIRED_CERTIFICATION_REVIEW_KINDS: Final[tuple[str, ...]] = (
    "certification_review_note",
    "certification_readiness_review_note",
    "certification_evidence_review_note",
)

GOVERNED_END_TO_END_DELIVERY_CERTIFICATION_RECORD_KINDS: Final[tuple[str, ...]] = (
    *REQUIRED_CERTIFICATION_REVIEW_KINDS,
    *HUMAN_CERTIFICATION_DECISION_KINDS,
    "certification_run_executed_note",
    "governed_end_to_end_delivery_certification_record",
)

GOVERNED_END_TO_END_DELIVERY_CERTIFICATION_PRINCIPLES: Final[tuple[tuple[str, str], ...]] = (
    ("certification_not_authority", "Delivery certification ≠ delivery authority."),
    ("evidence_backed", "Certification requires evidence from ET1–ET4 receipts."),
    ("repeatable", "Certification runs must be repeatable and measurable."),
    ("human_mandatory", "Human certification review remains mandatory."),
    ("no_trust_mutation", "Certification does not mutate trust."),
    ("no_auto_promotion", "No automatic certification promotion."),
    ("no_deployment_bypass", "No deployment bypass from certification layer."),
    ("no_approval_bypass", "No approval bypass from certification layer."),
    ("no_authority_escalation", "No authority escalation from certification layer."),
    ("multi_scenario", "Certification spans multiple governed delivery scenarios."),
)

FORBIDDEN_CERTIFICATION_ACTIONS: Final[tuple[tuple[str, str], ...]] = (
    ("trust_mutation", "Never mutate trust from certification layer."),
    ("automatic_promotion", "Never promote certification status automatically."),
    ("deployment_bypass", "Never bypass deployment governance from certification."),
    ("approval_bypass", "Never bypass human approvals from certification."),
    ("authority_escalation", "Never escalate delivery authority from certification."),
)

TRACK_NON_GOALS: Final[tuple[str, ...]] = (
    "no_trust_mutation",
    "no_automatic_certification_promotion",
    "no_deployment_bypass",
    "no_approval_bypass",
    "no_authority_escalation",
)

MAX_GOVERNED_END_TO_END_DELIVERY_CERTIFICATION_CONTENT_LEN: Final[int] = 8000
MAX_PERSISTED_GOVERNED_END_TO_END_DELIVERY_CERTIFICATION_RECORDS: Final[int] = 500

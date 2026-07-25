# SPDX-License-Identifier: Apache-2.0
"""PHASE_J1 / FIX 364 — production reality & longitudinal operations program contract."""

from __future__ import annotations

from typing import Final

PRODUCTION_REALITY_LONGITUDINAL_OPERATIONS_PROGRAM_ID: Final[str] = "PHASE_J1"
PRODUCTION_REALITY_LONGITUDINAL_OPERATIONS_PROGRAM_FIX: Final[str] = "FIX 364"
PRODUCTION_REALITY_LONGITUDINAL_OPERATIONS_PROGRAM_SCHEMA_VERSION: Final[str] = (
    "phase_production_reality_longitudinal_operations_program_v1"
)
PRODUCTION_REALITY_LONGITUDINAL_OPERATIONS_PROGRAM_RECORD_SCHEMA_VERSION: Final[str] = (
    "phase_production_reality_longitudinal_operations_program_record_v1"
)

CORE_PRINCIPLE: Final[str] = (
    "production_reality_measurement_measures_operational_durability_without_operational_authority"
)

MUTATION_PERFORMED_FIX_364: Final[bool] = False
GOVERNANCE_MUTATION_PERFORMED_FIX_364: Final[bool] = False
OPERATIONAL_AUTHORITY_FIX_364: Final[bool] = False
AUTONOMOUS_PRODUCTION_CONTROL_FIX_364: Final[bool] = False
AUTHORITY_EXPANSION_FIX_364: Final[bool] = False
GOVERNANCE_MUTATION_FIX_364: Final[bool] = False
GOVERNANCE_BYPASS_FIX_364: Final[bool] = False
TRUST_PROMOTION_FIX_364: Final[bool] = False
APPROVAL_BYPASS_FIX_364: Final[bool] = False
OPERATIONAL_AUTOMATION_CHANGES_FIX_364: Final[bool] = False
GOVERNANCE_BYPASS_AUTHORITY_FIX_364: Final[bool] = False
TRUST_MUTATION_AUTHORITY_FIX_364: Final[bool] = False
LOCAL_PRODUCTION_REALITY_LONGITUDINAL_OPERATIONS_EXECUTABLE_FIX_364: Final[bool] = True

PRODUCTION_REALITY_LONGITUDINAL_OPERATIONS_PROGRAM_ROUTE_ID: Final[str] = (
    "phase_production_reality_longitudinal_operations_program"
)

PRODUCTION_REALITY_LONGITUDINAL_OPERATIONS_PROGRAM_INVARIANT: Final[str] = (
    "production_reality_measurement_without_operational_authority_governance_mutation_or_trust_promotion"
)

PRODUCTION_REALITY_LONGITUDINAL_OPERATIONS_PHASES: Final[tuple[str, ...]] = (
    "phase_1_production_operations_registry",
    "phase_2_deployment_durability_analysis",
    "phase_3_incident_reality_analysis",
    "phase_4_recovery_durability_analysis",
    "phase_5_provider_reality_analysis",
    "phase_6_customer_reality_analysis",
    "phase_7_durability_opportunity_registry",
    "phase_8_executive_visibility",
    "phase_9_human_review",
)

DURABILITY_LEVELS: Final[tuple[str, ...]] = (
    "demonstrated",
    "sustained",
    "reliable",
    "durable",
    "production_proven",
)

OPERATION_CATEGORIES: Final[tuple[str, ...]] = (
    "deployment",
    "customer",
    "autonomous_run",
    "provider",
    "incident",
    "recovery",
)

PROVIDER_CATEGORIES: Final[tuple[str, ...]] = (
    "Railway",
    "Vercel",
    "AWS",
    "Kubernetes",
    "Azure",
    "GCP",
)

PRODUCTION_REALITY_METRICS: Final[tuple[str, ...]] = (
    "deployment_durability_score",
    "recovery_durability_score",
    "provider_durability_score",
    "customer_durability_score",
    "operational_durability_score",
)

EXECUTIVE_WORKSTREAM_MODULES: Final[tuple[str, ...]] = (
    "PHASE_I3",
    "WORKSTREAM_G4",
    "WORKSTREAM_H3",
    "FIX_330",
    "WORKSTREAM_F7",
)

HUMAN_PRODUCTION_REALITY_DECISION_KINDS: Final[tuple[str, ...]] = (
    "production_reality_review_approve",
    "production_reality_review_hold",
    "production_reality_review_reject",
    "production_reality_review_defer",
)

PRODUCTION_REALITY_RECORD_KINDS: Final[tuple[str, ...]] = (
    "production_reality_note",
    "production_reality_observation_entry",
    *HUMAN_PRODUCTION_REALITY_DECISION_KINDS,
    "production_reality_record",
)

PRODUCTION_OPERATIONS_MIN_SIZE: Final[int] = 1
PRODUCTION_SUSTAINED_MIN_SIZE: Final[int] = 2

PROGRAM_NON_GOALS: Final[tuple[str, ...]] = (
    "no_authority_expansion",
    "no_governance_mutation",
    "no_trust_promotion",
    "no_autonomous_production_control",
    "no_approval_bypass",
    "no_operational_automation_changes",
)

FORBIDDEN_PRODUCTION_REALITY_ACTIONS: Final[tuple[tuple[str, str], ...]] = (
    ("operational_authority", "Never grant operational authority from production reality measurement."),
    ("autonomous_production_control", "Never control production systems from durability measurement."),
    ("authority_expansion", "Never expand authority from production reality measurement."),
    ("governance_mutation", "Never alter governance from production reality program."),
    ("governance_bypass", "Never bypass approvals from production reality measurement."),
    ("approval_bypass", "Never bypass human approvals from durability observation."),
    ("trust_promotion", "Never promote trust from production reality measurement."),
    ("operational_automation_changes", "Never change operational automation from durability measurement."),
)

MAX_PRODUCTION_REALITY_CONTENT_LEN: Final[int] = 8000
MAX_PERSISTED_PRODUCTION_REALITY_RECORDS: Final[int] = 500

# SPDX-License-Identifier: Apache-2.0
"""WORKSTREAM_E4 / FIX 346 — compose runtime guardrails program contract."""

from __future__ import annotations

from typing import Final

COMPOSE_RUNTIME_GUARDRAILS_PROGRAM_ID: Final[str] = "WORKSTREAM_E4"
COMPOSE_RUNTIME_GUARDRAILS_PROGRAM_FIX: Final[str] = "FIX 346"
COMPOSE_RUNTIME_GUARDRAILS_PROGRAM_SCHEMA_VERSION: Final[str] = (
    "workstream_compose_runtime_guardrails_program_v1"
)
COMPOSE_RUNTIME_GUARDRAILS_PROGRAM_RECORD_SCHEMA_VERSION: Final[str] = (
    "workstream_compose_runtime_guardrails_program_record_v1"
)

CORE_PRINCIPLE: Final[str] = (
    "runtime_guardrails_prevent_accidental_expensive_compose_without_evidence_reduction"
)

MUTATION_PERFORMED_FIX_346: Final[bool] = False
EXECUTION_PERFORMED_FIX_346: Final[bool] = True
EVIDENCE_REDUCTION_FIX_346: Final[bool] = False
TRUTH_MUTATION_FIX_346: Final[bool] = False
TRUST_MUTATION_AUTHORITY_FIX_346: Final[bool] = False
AUTHORITY_EXPANSION_FIX_346: Final[bool] = False
GOVERNANCE_BYPASS_AUTHORITY_FIX_346: Final[bool] = False
GOVERNANCE_MUTATION_PERFORMED_FIX_346: Final[bool] = False
LOCAL_RUNTIME_GUARDRAIL_EXECUTABLE_FIX_346: Final[bool] = True

COMPOSE_RUNTIME_GUARDRAILS_PROGRAM_ROUTE_ID: Final[str] = "workstream_compose_runtime_guardrails_program"

COMPOSE_RUNTIME_GUARDRAILS_PROGRAM_INVARIANT: Final[str] = (
    "compose_runtime_guardrails_without_evidence_reduction_or_governance_change"
)

COMPOSE_RUNTIME_GUARDRAILS_PHASES: Final[tuple[str, ...]] = (
    "phase_1_runtime_mode_registry",
    "phase_2_compose_cost_classification",
    "phase_3_heavy_compose_guard",
    "phase_4_test_runtime_safety",
    "phase_5_interactive_runtime_safety",
    "phase_6_benchmark_command_separation",
    "phase_7_timeout_warning_policy",
    "phase_8_runtime_safety_dashboard",
    "phase_9_human_review",
)

EXECUTIVE_FIX_MODULES: Final[tuple[str, ...]] = (
    "FIX 316",
    "FIX 324",
    "FIX 329",
    "FIX 330",
)

HUMAN_RUNTIME_GUARDRAIL_DECISION_KINDS: Final[tuple[str, ...]] = (
    "runtime_guardrail_review_approve",
    "runtime_guardrail_review_hold",
    "runtime_guardrail_review_reject",
    "runtime_guardrail_review_defer",
)

COMPOSE_RUNTIME_GUARDRAILS_RECORD_KINDS: Final[tuple[str, ...]] = (
    "runtime_guardrail_note",
    *HUMAN_RUNTIME_GUARDRAIL_DECISION_KINDS,
    "runtime_guardrail_enforcement_note",
    "compose_runtime_guardrails_program_record",
)

PROGRAM_NON_GOALS: Final[tuple[str, ...]] = (
    "no_evidence_deletion",
    "no_truth_reduction",
    "no_authority_expansion",
    "no_governance_bypass",
    "no_removal_of_full_compose_paths",
)

FORBIDDEN_GUARDRAIL_ACTIONS: Final[tuple[tuple[str, str], ...]] = (
    ("evidence_reduction", "Never remove evidence when enforcing runtime guardrails."),
    ("truth_reduction", "Never reduce truth quality via guardrails."),
    ("trust_mutation", "Never mutate trust from guardrail enforcement."),
    ("governance_bypass", "Never bypass governance via guardrail layer."),
    ("authority_expansion", "Never expand authority from guardrail program."),
)

MAX_COMPOSE_RUNTIME_GUARDRAILS_CONTENT_LEN: Final[int] = 8000
MAX_PERSISTED_COMPOSE_RUNTIME_GUARDRAILS_RECORDS: Final[int] = 500

# SPDX-License-Identifier: Apache-2.0
"""FIX 190 — agent execution quality and throughput metrics contract."""

from __future__ import annotations

from typing import Final

AGENT_EXECUTION_QUALITY_THROUGHPUT_METRICS_SCHEMA_VERSION: Final[str] = (
    "mission_control_agent_execution_quality_throughput_metrics_v1"
)
AGENT_EXECUTION_QUALITY_THROUGHPUT_METRICS_RECORD_SCHEMA_VERSION: Final[str] = (
    "mission_control_agent_execution_quality_throughput_metrics_record_v1"
)
AGENT_EXECUTION_QUALITY_THROUGHPUT_METRICS_FIX: Final[str] = "FIX 190"

MUTATION_PERFORMED_FIX_190: Final[bool] = False
EXECUTION_PERFORMED_FIX_190: Final[bool] = False
AGENT_METRICS_GRANT_AUTHORITY_FIX_190: Final[bool] = False
AGENT_EXECUTION_AUTHORITY_FIX_190: Final[bool] = False
MERGE_AUTHORITY_FIX_190: Final[bool] = False
DEPLOY_AUTHORITY_FIX_190: Final[bool] = False
RAILWAY_AUTHORITY_FIX_190: Final[bool] = False
PROVIDER_AUTHORITY_FIX_190: Final[bool] = False
GATE_BYPASS_ENABLED_FIX_190: Final[bool] = False
AUTONOMOUS_APPROVAL_ENABLED_FIX_190: Final[bool] = False
GOVERNANCE_MUTATION_PERFORMED_FIX_190: Final[bool] = False
METRICS_COMPOSE_RECEIPTS_ONLY_FIX_190: Final[bool] = True

AGENT_EXECUTION_QUALITY_THROUGHPUT_METRICS_ROUTE_ID: Final[str] = (
    "mission_control_agent_execution_quality_throughput_metrics"
)
AGENT_EXECUTION_QUALITY_THROUGHPUT_METRICS_ORIGIN: Final[str] = (
    "mission_control_agent_execution_quality_throughput_metrics"
)

AGENT_EXECUTION_QUALITY_THROUGHPUT_METRICS_INVARIANT: Final[str] = (
    "agent_execution_quality_throughput_metrics_compose_fix_189_receipts_without_agent_metrics_granting_authority_or_execution"
)

METRIC_AGENT_ROLE_IDS: Final[tuple[str, ...]] = (
    "planner_agent",
    "delivery_agent",
    "verification_agent",
    "diff_audit_agent",
    "risk_agent",
)

THROUGHPUT_METRIC_IDS: Final[tuple[str, ...]] = (
    "per_agent_execution_receipts",
    "time_per_agent",
    "success_failure_per_agent",
    "retry_count",
    "human_intervention_count",
    "alignment_score_contribution",
    "verification_contribution",
    "diff_audit_quality",
    "risk_scoring_consistency",
    "package_completion_rate",
    "end_to_end_throughput_score",
)

AGENT_EXECUTION_QUALITY_THROUGHPUT_METRICS_RECORD_KINDS: Final[tuple[str, ...]] = (
    "metrics_observation",
    "throughput_note",
    "quality_note",
    "human_intervention_note",
    "metrics_annotation",
    "agent_execution_quality_throughput_metrics_record",
)

AGENT_EXECUTION_QUALITY_THROUGHPUT_METRICS_PRINCIPLES: Final[tuple[tuple[str, str], ...]] = (
    ("metrics_not_authority", "Agent metrics ≠ agent authority."),
    ("compose_fix_189_only", "Metrics compose FIX 189 execution receipts — no new execution."),
    ("no_gate_bypass", "Metrics never bypass frozen gates."),
    ("no_merge_deploy", "Metrics never grant merge, deploy, Railway, or provider authority."),
    ("throughput_evidence", "Throughput score measures delivery improvement evidence only."),
    ("human_intervention_visible", "Human intervention count tracks operator touches separately from agent work."),
    ("quality_before_scale", "Quality metrics required before scaling multi-agent delivery cross-repo."),
    ("read_only_composition", "Metrics assembly is read-only cognition."),
)

FORBIDDEN_METRICS_ACTIONS: Final[tuple[tuple[str, str], ...]] = (
    ("agent_execution_authority", "Metrics never grant agent execution authority."),
    ("merge_deploy", "Metrics never grant merge or deploy authority."),
    ("railway_mutation", "Metrics never grant Railway authority."),
    ("provider_mutation", "Metrics never grant provider authority."),
    ("gate_bypass", "Metrics never bypass gates."),
    ("hidden_execution", "Metrics never trigger hidden execution paths."),
    ("autonomous_approval", "Metrics never auto-approve human decisions."),
    ("metrics_as_trust_grant", "Metrics scores are not trust grants."),
)

AGENT_EXECUTION_QUALITY_THROUGHPUT_METRICS_EXECUTABLE: Final[bool] = False

MAX_AGENT_EXECUTION_QUALITY_THROUGHPUT_METRICS_CONTENT_LEN: Final[int] = 4000
MAX_PERSISTED_AGENT_EXECUTION_QUALITY_THROUGHPUT_METRICS_RECORDS: Final[int] = 500

# SPDX-License-Identifier: Apache-2.0
"""FIX 119 — production runtime verification contract (schema + signal taxonomy)."""

from __future__ import annotations

from typing import Final, Literal

SignalStrength = Literal["weak", "medium", "strong"]
RollbackRecommendation = Literal[
    "none",
    "advise_manual_review",
    "advise_shadow_rollback_rehearsal",
    "advise_incident_escalation",
    "blocked_pending_evidence",
]
IncidentEscalationLevel = Literal["none", "operator_review", "incident_commander", "executive_bridge"]

PRODUCTION_VERIFICATION_RECEIPT_PHASE: Final[str] = "production_runtime_verification"
PRODUCTION_VERIFICATION_SHADOW_PHASE: Final[str] = "verify_runtime_shadow"

REQUIRED_SIGNAL_FAMILIES: Final[tuple[str, ...]] = (
    "slo",
    "health_check",
    "deployment",
)

STRONG_SIGNAL_IDS: Final[frozenset[str]] = frozenset(
    {
        "slo_availability_budget_met",
        "slo_latency_budget_met",
        "health_check_multi_probe_agreement",
        "deployment_log_success_pattern",
        "deployment_state_confirmed",
    }
)

WEAK_ONLY_SIGNAL_IDS: Final[frozenset[str]] = frozenset(
    {
        "deployment_state_only",
        "health_check_path_configured_only",
    }
)

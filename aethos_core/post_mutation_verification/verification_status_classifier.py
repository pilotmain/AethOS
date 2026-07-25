# SPDX-License-Identifier: Apache-2.0
"""Classify post-mutation verification status from evidence."""

from __future__ import annotations

from typing import Literal

from aethos_core.post_mutation_verification.before_after_comparator import BeforeAfterComparison
from aethos_core.post_mutation_verification.verification_evidence_collector import VerificationEvidence

VerificationStatus = Literal[
    "verified",
    "unconfirmed",
    "still_stabilizing",
    "failed_after_mutation",
    "regressed",
    "blocked_by_missing_evidence",
]


def classify_verification_status(
    evidence: VerificationEvidence,
    comparison: BeforeAfterComparison,
) -> VerificationStatus:
    if not evidence.execution_completed:
        return "blocked_by_missing_evidence"

    restart_state = evidence.restart_verification_state.lower()
    ver_state = evidence.verification_state.lower()

    if restart_state in {"stabilizing", "restart_requested"} and not comparison.health_unchanged_failed:
        if ver_state in {"verification_running", "verification_pending"} and not evidence.low_signal_logs:
            return "still_stabilizing"

    if evidence.verified_flag or ver_state == "verified" or restart_state in {
        "restart_transition_detected",
        "log_restart_detected",
    }:
        if comparison.health_unchanged_failed and not comparison.health_improved:
            return "failed_after_mutation"
        return "verified"

    if restart_state in {"stabilizing", "restart_requested"} or ver_state in {
        "verification_running",
        "verification_pending",
    }:
        if not comparison.health_unchanged_failed and not evidence.low_signal_logs:
            return "still_stabilizing"

    if comparison.new_crash_after_restart or (
        comparison.health_unchanged_failed and evidence.new_crash_detected
    ):
        if comparison.before_status and comparison.after_status:
            if _failed(comparison.before_status) and _failed(comparison.after_status):
                return "regressed"
        return "failed_after_mutation"

    if comparison.health_unchanged_failed or _failed(comparison.after_status) or _failed(comparison.after_health):
        return "failed_after_mutation"

    if not evidence.logs_after_execution and not evidence.provider_command_submitted:
        return "blocked_by_missing_evidence"

    if evidence.low_signal_logs or restart_state in {
        "restart_unverified",
        "service_online_but_restart_unproven",
    }:
        return "unconfirmed"

    if comparison.health_improved:
        return "verified"

    return "unconfirmed"


def verification_status_label(status: VerificationStatus) -> str:
    return status.replace("_", " ")


def _failed(value: str) -> bool:
    low = str(value or "").lower()
    return low in {"failed", "crashed", "error", "unhealthy"}

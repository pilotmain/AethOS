# SPDX-License-Identifier: Apache-2.0
"""Canonical mutation lifecycle states — execution ≠ verified."""

from __future__ import annotations

from typing import Any


EXECUTION_QUEUED = "queued"
EXECUTION_EXECUTING = "executing"
EXECUTION_MUTATION_REQUESTED = "provider_mutation_requested"
EXECUTION_STABILIZING = "stabilizing"
EXECUTION_COMPLETED = "execution_completed"
EXECUTION_FAILED = "execution_failed"

VERIFICATION_PENDING = "verification_pending"
VERIFICATION_RUNNING = "verification_running"
VERIFICATION_VERIFIED = "verified"
VERIFICATION_FAILED = "verification_failed"
VERIFICATION_TIMEOUT = "verification_timeout"
VERIFICATION_INCONCLUSIVE = "verification_inconclusive"

LIFECYCLE_STABILIZING = "stabilizing"
LIFECYCLE_MUTATION_REQUESTED = "provider_mutation_requested"
LIFECYCLE_AWAITING_APPROVAL = "awaiting_approval"
LIFECYCLE_EXECUTING = "executing"
LIFECYCLE_EXECUTION_COMPLETED = "execution_completed"
LIFECYCLE_VERIFICATION_RUNNING = "verification_running"
LIFECYCLE_VERIFIED = "verified"
LIFECYCLE_VERIFICATION_FAILED = "verification_failed"
LIFECYCLE_ROLLBACK_REQUIRED = "rollback_required"
LIFECYCLE_EXECUTION_FAILED = "execution_failed"
LIFECYCLE_AUDIT_RECORDED = "audit_recorded"


def execution_state_after_provider_response(*, provider_accepted: bool, result: dict[str, Any] | None = None) -> str:
    if not provider_accepted:
        return EXECUTION_FAILED
    explicit = str((result or {}).get("execution_state") or "")
    if explicit in {EXECUTION_MUTATION_REQUESTED, EXECUTION_STABILIZING}:
        return explicit
    return EXECUTION_MUTATION_REQUESTED


def lifecycle_after_provider_response(*, provider_accepted: bool) -> str:
    return LIFECYCLE_STABILIZING if provider_accepted else LIFECYCLE_EXECUTION_FAILED


def execution_state_after_run(*, executed: bool) -> str:
    return EXECUTION_COMPLETED if executed else EXECUTION_FAILED


def verification_state_after_enqueue() -> str:
    return VERIFICATION_PENDING


def lifecycle_after_execution(*, executed: bool) -> str:
    return LIFECYCLE_EXECUTION_COMPLETED if executed else LIFECYCLE_EXECUTION_FAILED


def lifecycle_after_verification(
    *,
    verification_result: str,
    failure_type: str | None = None,
) -> tuple[str, str]:
    """Return (verification_state, lifecycle_state)."""
    if verification_result == "healthy":
        return VERIFICATION_VERIFIED, LIFECYCLE_VERIFIED
    if verification_result == "pending":
        return VERIFICATION_RUNNING, LIFECYCLE_VERIFICATION_RUNNING
    if verification_result == "inconclusive":
        return VERIFICATION_INCONCLUSIVE, LIFECYCLE_VERIFICATION_FAILED
    if failure_type == "verification_timeout":
        return VERIFICATION_TIMEOUT, LIFECYCLE_ROLLBACK_REQUIRED
    return VERIFICATION_FAILED, LIFECYCLE_ROLLBACK_REQUIRED if verification_result == "unhealthy" else LIFECYCLE_VERIFICATION_FAILED

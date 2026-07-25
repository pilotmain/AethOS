# SPDX-License-Identifier: Apache-2.0
"""Canonical mutation failure taxonomy."""

from __future__ import annotations

EXECUTION_FAILED = "execution_failed"
VERIFICATION_FAILED = "verification_failed"
APPROVAL_DENIED = "approval_denied"
PROVIDER_TIMEOUT = "provider_timeout"
PROVIDER_AUTH_FAILURE = "provider_auth_failure"
TARGET_UNRESOLVED = "target_unresolved"
VERIFICATION_TIMEOUT = "verification_timeout"
ROLLBACK_REQUIRED = "rollback_required"
POLICY_BLOCKED = "policy_blocked"
UNSUPPORTED_OPERATION = "unsupported_operation"
WORKFLOW_NOT_FOUND = "workflow_not_found"
RERUN_NOT_SUPPORTED = "rerun_not_supported"
NO_RERUNNABLE_CANDIDATE = "no_rerunnable_candidate"
RUN_NOT_DETECTED = "run_not_detected"
DISCOVERY_FAILED = "discovery_failed"
VERIFICATION_INCONCLUSIVE = "verification_inconclusive"


def classify_github_rerun_failure(*, error_text: str, http_status: int | None = None) -> str:
    lower = (error_text or "").lower()
    if http_status == 401 or http_status == 403 or "bad credentials" in lower or "401" in lower:
        return PROVIDER_AUTH_FAILURE
    if http_status == 404 or "not found" in lower:
        return WORKFLOW_NOT_FOUND
    if "timeout" in lower:
        return PROVIDER_TIMEOUT
    if "rerun" in lower and "not" in lower:
        return RERUN_NOT_SUPPORTED
    return EXECUTION_FAILED


def classify_verification_failure(*, reason: str) -> str:
    lower = (reason or "").lower()
    if "timeout" in lower:
        return VERIFICATION_TIMEOUT
    if "not detected" in lower or "run_not" in lower:
        return RUN_NOT_DETECTED
    return VERIFICATION_FAILED

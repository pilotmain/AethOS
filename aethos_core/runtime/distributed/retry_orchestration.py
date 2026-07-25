# SPDX-License-Identifier: Apache-2.0
"""Retry orchestration — bounded retries with governance."""

from __future__ import annotations

from typing import Any

MAX_RETRIES = 3
RETRYABLE_DOMAINS = frozenset(
    {"verification_retry", "telemetry_refresh", "replay_reconstruct", "provider_poll", "validation"}
)


def plan_retry(*, domain: str, attempt: int, last_error: str | None = None) -> dict[str, Any]:
    """Plan bounded retry — never hidden or autonomous."""
    if domain not in RETRYABLE_DOMAINS:
        return {"ok": False, "error": "domain_not_retryable", "autonomous_execution_blocked": True}
    if attempt >= MAX_RETRIES:
        return {
            "ok": False,
            "error": "max_retries_exceeded",
            "attempt": attempt,
            "max_retries": MAX_RETRIES,
            "autonomous_execution_blocked": True,
        }
    return {
        "ok": True,
        "attempt": attempt + 1,
        "max_retries": MAX_RETRIES,
        "backoff_seconds": min(2 ** attempt * 5, 60),
        "approval_required": domain in ("verification_retry",),
        "last_error": last_error,
        "autonomous_execution_blocked": True,
    }

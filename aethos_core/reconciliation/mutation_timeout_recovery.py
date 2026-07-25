# SPDX-License-Identifier: Apache-2.0
"""Mutation timeout recovery — hung execution detection."""

from __future__ import annotations

from typing import Any


def assess_timeout_recovery(*, job: Any) -> dict[str, Any]:
    params = getattr(job, "params", {}) or {}
    reason = str(params.get("status_reason") or params.get("failure_reason") or "")
    timed_out = "timeout" in reason.lower() or "timed out" in reason.lower()
    return {
        "timeout_detected": timed_out,
        "recovery_recommended": timed_out,
        "summary": "Hung execution detected — reconciliation recovery recommended." if timed_out else "No timeout condition detected.",
    }

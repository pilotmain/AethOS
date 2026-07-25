# SPDX-License-Identifier: Apache-2.0
"""Execution convergence — execution vs verified state alignment."""

from __future__ import annotations

from typing import Any


def assess_execution_convergence(
    *,
    events: list[dict[str, Any]] | None = None,
    verification: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Measure alignment between reported execution and verified outcomes."""
    rows = list(events or [])
    executed_count = sum(1 for e in rows if e.get("executed") or "execut" in str(e.get("summary", "")).lower())
    verified_count = sum(1 for e in rows if e.get("verified") or "verified" in str(e.get("summary", "")).lower())
    failure_count = sum(
        1
        for e in rows
        if any(k in str(e.get("summary", "")).lower() for k in ("fail", "restart", "rerun", "instability"))
    )

    ver = verification or {}
    verified = bool(ver.get("verified"))
    executed = bool(ver.get("executed")) or executed_count > 0

    if executed and verified and failure_count == 0:
        state = "converged"
    elif executed and not verified:
        state = "execution_unverified"
    elif failure_count >= 3:
        state = "divergent_failures"
    elif failure_count >= 1:
        state = "partial_convergence"
    else:
        state = "unknown"

    ratio = round(verified_count / max(executed_count, 1), 2) if executed_count else 0.0
    return {
        "convergence_state": state,
        "executed": executed,
        "verified": verified,
        "executed_count": executed_count,
        "verified_count": verified_count,
        "failure_count": failure_count,
        "convergence_ratio": ratio,
        "summary": f"Execution convergence: {state} (failures={failure_count}).",
    }

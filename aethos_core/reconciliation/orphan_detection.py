# SPDX-License-Identifier: Apache-2.0
"""Orphan detection — incomplete execution states."""

from __future__ import annotations

from typing import Any


def detect_orphan_state(*, job: Any, verification: dict[str, Any]) -> dict[str, Any]:
    lifecycle = str(getattr(job, "params", {}).get("lifecycle_state") or "")
    execution = str(getattr(job, "params", {}).get("execution_state") or getattr(job, "status", ""))
    orphan = execution in ("completed", "execution_completed") and not verification.get("verified") and lifecycle not in (
        "verification_verified",
        "verified",
    )
    return {
        "orphan_detected": orphan,
        "lifecycle_state": lifecycle,
        "execution_state": execution,
        "summary": "Incomplete execution state detected — reconciliation required." if orphan else "No orphan execution state.",
    }

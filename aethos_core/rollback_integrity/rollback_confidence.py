# SPDX-License-Identifier: Apache-2.0
"""Rollback confidence — bounded rollback trust."""

from __future__ import annotations

from typing import Any

from aethos_core.rollback_integrity.rollback_reconciliation import reconcile_rollback


def score_rollback_confidence(*, provider_result: dict[str, Any] | None = None, readonly_artifact: dict[str, Any] | None = None) -> dict[str, Any]:
    recon = reconcile_rollback(provider_result=provider_result, readonly_artifact=readonly_artifact)
    verified = bool(recon.get("rollback_verified"))
    score = 0.88 if verified else 0.62
    return {
        "rollback_verified": verified,
        "rollback_confidence": score,
        "reconciliation": recon,
        "summary": "Rollback integrity verified with bounded confidence." if verified else "Rollback integrity partially verified.",
    }

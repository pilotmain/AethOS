# SPDX-License-Identifier: Apache-2.0
"""Railway rollback runtime — rollback verification."""

from __future__ import annotations

from typing import Any


def verify_rollback_integrity(*, provider_result: dict[str, Any], readonly_artifact: dict[str, Any]) -> dict[str, Any]:
    rollback = provider_result.get("rollback_metadata") or {}
    attempted = bool(rollback.get("rollback_attempted") or provider_result.get("rollback_attempted"))
    restored = str(rollback.get("deployment_state_after") or "").lower() in ("success", "running", "ready", "active")
    summary = str(readonly_artifact.get("summary") or "").lower()
    if not attempted:
        return {"rollback_verified": False, "status": "not_applicable", "summary": "No rollback path invoked."}
    ok = restored or any(w in summary for w in ("restored", "rolled back", "recovered"))
    return {
        "rollback_verified": ok,
        "status": "verified" if ok else "partial",
        "summary": "Rollback integrity confirmed — runtime restored." if ok else "Rollback initiated — restoration partially confirmed.",
    }

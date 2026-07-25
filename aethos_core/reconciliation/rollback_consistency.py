# SPDX-License-Identifier: Apache-2.0
"""Rollback consistency — rollback integrity validation."""

from __future__ import annotations

from typing import Any


def assess_rollback_consistency(*, provider_result: dict[str, Any], readonly_artifact: dict[str, Any]) -> dict[str, Any]:
    if provider_result.get("provider") == "railway":
        from aethos_core.providers.railway.hardening.rollback_runtime import verify_rollback_integrity

        return verify_rollback_integrity(provider_result=provider_result, readonly_artifact=readonly_artifact)
    summary = str(readonly_artifact.get("summary") or "").lower()
    restored = any(w in summary for w in ("restored", "rollback", "recovered"))
    return {"rollback_verified": restored, "status": "verified" if restored else "partial", "summary": "Rollback consistency assessed."}

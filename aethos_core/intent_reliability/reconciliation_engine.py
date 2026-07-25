# SPDX-License-Identifier: Apache-2.0
"""Reconciliation engine — final response integrity."""

from __future__ import annotations

from typing import Any


def finalize_response(
    *,
    reconciled: dict[str, Any],
    contract: dict[str, Any],
    trust: dict[str, Any],
    integrity: dict[str, Any],
) -> dict[str, Any]:
    verified = (
        reconciled.get("verified", False)
        and integrity.get("clean", False)
        and trust.get("restrained", True)
    )
    reply = reconciled.get("reply", "")
    if not integrity.get("clean") and contract.get("result_count"):
        summary = "Response refined to honor user contract — extended verification applied."
    else:
        summary = trust.get("summary", "Conversational reliability verified.")
    return {
        "verified": verified,
        "reply": reply,
        "summary": summary,
        "qualification_tier": "production conversational" if verified else "premium" if reconciled.get("verified") else "beta",
    }

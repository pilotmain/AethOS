# SPDX-License-Identifier: Apache-2.0
"""Operational fatigue / repetition analysis — Phase 11.8.2."""

from __future__ import annotations

from typing import Any

from aethos_core.telegram_soak.session_truth_ledger import list_ledger_entries


def assess_operational_fatigue(*, session_id: str = "default") -> dict[str, Any]:
    entries = list_ledger_entries(session_id=session_id, limit=50)
    if len(entries) < 3:
        return {"ok": True, "fatigue": "none", "qualified": True}
    previews = [str(e.get("reply_preview") or "")[:120] for e in entries[:10]]
    unique = len(set(previews))
    ratio = unique / max(len(previews), 1)
    fatigue = "none"
    if ratio < 0.4:
        fatigue = "high"
    elif ratio < 0.7:
        fatigue = "moderate"
    return {
        "ok": True,
        "fatigue": fatigue,
        "unique_reply_ratio": round(ratio, 2),
        "qualified": fatigue != "high",
    }

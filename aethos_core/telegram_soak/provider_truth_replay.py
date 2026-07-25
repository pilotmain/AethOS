# SPDX-License-Identifier: Apache-2.0
"""Provider truth replay timelines — Phase 11.8.2."""

from __future__ import annotations

from typing import Any

from aethos_core.telegram_soak.session_truth_ledger import list_ledger_entries


def build_provider_truth_replay(*, session_id: str = "default") -> dict[str, Any]:
    entries = list_ledger_entries(session_id=session_id, limit=100)
    timeline = [
        {
            "timestamp": e.get("timestamp"),
            "scenario_id": e.get("scenario_id"),
            "user_text": e.get("user_text"),
            "operational_realism_score": e.get("operational_realism_score"),
            "hallucination_risk": e.get("hallucination_risk"),
        }
        for e in reversed(entries)
    ]
    return {"ok": True, "session_id": session_id, "timeline": timeline, "event_count": len(timeline)}

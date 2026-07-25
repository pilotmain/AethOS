# SPDX-License-Identifier: Apache-2.0
"""Transcript capture — Phase 11.8.2."""

from __future__ import annotations

from typing import Any

from aethos_core.telegram_soak.realism_scoring import score_turn
from aethos_core.telegram_soak.session_truth_ledger import append_ledger_entry


def capture_turn(
    *,
    session_id: str,
    scenario_id: str,
    user_text: str,
    reply: str,
    mode: str = "compressed",
) -> dict[str, Any]:
    scores = score_turn(reply=reply, scenario_id=scenario_id, user_text=user_text)
    entry = append_ledger_entry(
        session_id=session_id,
        scenario_id=scenario_id,
        user_text=user_text,
        reply=reply,
        scores=scores,
        mode=mode,
    )
    return {"ok": True, "entry": entry, "scores": scores}

# SPDX-License-Identifier: Apache-2.0
"""Session truth ledger — Phase 11.8.2."""

from __future__ import annotations

import json
from pathlib import Path
from time import time
from typing import Any
from uuid import uuid4


def _ledger_path(session_id: str) -> Path:
    root = Path(__file__).resolve().parents[2] / "data" / "conversation" / "telegram_soak"
    root.mkdir(parents=True, exist_ok=True)
    safe = session_id.replace("/", "_")[:80]
    return root / f"ledger_{safe}.json"


def append_ledger_entry(
    *,
    session_id: str,
    scenario_id: str,
    user_text: str,
    reply: str,
    scores: dict[str, Any],
    mode: str = "compressed",
) -> dict[str, Any]:
    entry = {
        "entry_id": f"tl-{uuid4().hex[:10]}",
        "timestamp": time(),
        "scenario_id": scenario_id,
        "user_text": user_text[:500],
        "reply_preview": reply[:800],
        "mode": mode,
        **scores,
    }
    path = _ledger_path(session_id)
    rows: list[dict[str, Any]] = []
    if path.is_file():
        try:
            rows = list(json.loads(path.read_text(encoding="utf-8")))
        except (OSError, json.JSONDecodeError):
            rows = []
    rows.insert(0, entry)
    path.write_text(json.dumps(rows[:200], indent=2), encoding="utf-8")
    return entry


def list_ledger_entries(*, session_id: str, limit: int = 50) -> list[dict[str, Any]]:
    path = _ledger_path(session_id)
    if not path.is_file():
        return []
    try:
        return list(json.loads(path.read_text(encoding="utf-8")))[:limit]
    except (OSError, json.JSONDecodeError):
        return []


def summarize_ledger(*, session_id: str) -> dict[str, Any]:
    entries = list_ledger_entries(session_id=session_id, limit=100)
    if not entries:
        return {"ok": True, "session_id": session_id, "entry_count": 0, "average_realism": 0}
    realism = [float(e.get("operational_realism_score") or 0) for e in entries]
    avg = round(sum(realism) / max(len(realism), 1), 3)
    return {
        "ok": True,
        "session_id": session_id,
        "entry_count": len(entries),
        "average_realism": avg,
        "latest": entries[0],
        "entries": entries[:20],
    }


def clear_ledger_for_tests(*, session_id: str | None = None) -> None:
    root = Path(__file__).resolve().parents[2] / "data" / "conversation" / "telegram_soak"
    if session_id:
        path = _ledger_path(session_id)
        if path.is_file():
            path.unlink()
        return
    if root.is_dir():
        for p in root.glob("ledger_*.json"):
            p.unlink()

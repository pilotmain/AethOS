# SPDX-License-Identifier: Apache-2.0
"""Pinned research notes — Notes pattern per session."""

from __future__ import annotations

import json
import re
from pathlib import Path
from time import time
from typing import Any
from uuid import uuid4

_MAX_NOTES = 40
_SESSION_RE = re.compile(r"[^a-zA-Z0-9._-]+")


def _sanitize(session_id: str) -> str:
    raw = (session_id or "default").strip()[:64]
    cleaned = _SESSION_RE.sub("-", raw).strip("-")
    return cleaned or "default"


def _root() -> Path:
    root = Path("data/research_artifacts/notes").expanduser()
    root.mkdir(parents=True, exist_ok=True)
    return root


def _path(session_id: str) -> Path:
    return _root() / f"{_sanitize(session_id)}.json"


def list_notes(*, session_id: str | None = None, limit: int = 20) -> dict[str, Any]:
    cap = max(1, min(limit, _MAX_NOTES))
    if session_id:
        rows = _load_session(session_id)
        return {"ok": True, "session_id": _sanitize(session_id), "notes": rows[:cap]}
    all_rows: list[dict[str, Any]] = []
    for path in sorted(_root().glob("*.json"), key=lambda p: p.stat().st_mtime, reverse=True):
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
            if isinstance(payload, list):
                all_rows.extend(row for row in payload if isinstance(row, dict))
        except (OSError, json.JSONDecodeError):
            continue
        if len(all_rows) >= cap:
            break
    all_rows.sort(key=lambda r: float(r.get("updated_at") or 0), reverse=True)
    return {"ok": True, "notes": all_rows[:cap]}


def _load_session(session_id: str) -> list[dict[str, Any]]:
    path = _path(session_id)
    if not path.is_file():
        return []
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
        if isinstance(raw, list):
            return [row for row in raw if isinstance(row, dict)]
    except (OSError, json.JSONDecodeError):
        return []
    return []


def pin_note(
    *,
    session_id: str,
    text: str,
    replay_id: str | None = None,
    query: str | None = None,
) -> dict[str, Any]:
    body = (text or "").strip()
    if not body:
        return {"ok": False, "error": "text_required"}
    sid = _sanitize(session_id)
    now = time()
    row = {
        "id": f"note-{uuid4().hex[:10]}",
        "session_id": sid,
        "text": body[:4000],
        "replay_id": (replay_id or "").strip() or None,
        "query": (query or "").strip()[:500] or None,
        "created_at": now,
        "updated_at": now,
    }
    rows = _load_session(sid)
    rows.insert(0, row)
    _path(sid).write_text(json.dumps(rows[:_MAX_NOTES], indent=2), encoding="utf-8")
    return {"ok": True, "note": row}


def delete_note(*, session_id: str, note_id: str) -> dict[str, Any]:
    sid = _sanitize(session_id)
    nid = (note_id or "").strip()
    rows = [r for r in _load_session(sid) if str(r.get("id")) != nid]
    if len(rows) == len(_load_session(sid)):
        return {"ok": False, "error": "not_found"}
    _path(sid).write_text(json.dumps(rows[:_MAX_NOTES], indent=2), encoding="utf-8")
    return {"ok": True, "deleted_id": nid}

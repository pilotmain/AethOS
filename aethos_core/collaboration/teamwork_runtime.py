# SPDX-License-Identifier: Apache-2.0
"""Human-agent teamwork runtime — persistent collaboration rooms."""

from __future__ import annotations

import json
from time import time
from typing import Any
from uuid import uuid4

from pathlib import Path


def _teamwork_root() -> Path:
    root = Path(__file__).resolve().parents[2] / "data" / "collaboration" / "teamwork"
    root.mkdir(parents=True, exist_ok=True)
    return root


def _rooms_path() -> Path:
    return _teamwork_root() / "rooms.json"


def _load_rooms() -> list[dict[str, Any]]:
    path = _rooms_path()
    if not path.is_file():
        return []
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return []


def _save_rooms(rows: list[dict[str, Any]]) -> None:
    _rooms_path().write_text(json.dumps(rows[:40], indent=2), encoding="utf-8")


def create_collaboration_room(
    *,
    operator_id: str = "default",
    title: str = "Investigation",
    focus: str = "debugging",
) -> dict[str, Any]:
    room_id = f"room-{uuid4().hex[:10]}"
    record = {
        "room_id": room_id,
        "title": title,
        "focus": focus,
        "operator_id": operator_id,
        "status": "active",
        "evidence_board": [],
        "delegation_map": [],
        "checkpoints": [],
        "started_at": time(),
        "human_authoritative": True,
        "autonomous_execution_blocked": True,
    }
    rows = _load_rooms()
    rows.insert(0, record)
    _save_rooms(rows)
    return {"ok": True, "room": record, "principle": "AethOS amplifies operators — it does not replace them."}


def add_evidence_to_room(*, room_id: str, evidence: str, source: str = "operator") -> dict[str, Any]:
    rows = _load_rooms()
    for row in rows:
        if row.get("room_id") == room_id:
            item = {"text": evidence[:400], "source": source, "at": time()}
            row.setdefault("evidence_board", []).append(item)
            _save_rooms(rows)
            return {"ok": True, "evidence": item}
    return {"ok": False, "reason": "Room not found."}


def record_delegation(*, room_id: str, from_agent: str, to_agent: str, scope: str) -> dict[str, Any]:
    rows = _load_rooms()
    for row in rows:
        if row.get("room_id") == room_id:
            item = {"from": from_agent, "to": to_agent, "scope": scope[:200], "visible": True, "at": time()}
            row.setdefault("delegation_map", []).append(item)
            _save_rooms(rows)
            return {"ok": True, "delegation": item}
    return {"ok": False, "reason": "Room not found."}


def list_collaboration_rooms(*, operator_id: str | None = None) -> dict[str, Any]:
    rows = _load_rooms()
    if operator_id:
        rows = [r for r in rows if r.get("operator_id") == operator_id]
    return {
        "ok": True,
        "rooms": rows,
        "features": {
            "persistent_collaboration_rooms": True,
            "shared_evidence_boards": True,
            "agent_delegation_maps": True,
            "collaborative_debugging": True,
            "handoff_continuity": True,
            "execution_checkpoints": True,
        },
        "autonomous_execution_blocked": True,
    }


def clear_teamwork_for_tests() -> None:
    path = _rooms_path()
    if path.is_file():
        path.unlink()

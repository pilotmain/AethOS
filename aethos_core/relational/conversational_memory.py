# SPDX-License-Identifier: Apache-2.0
"""Conversational memory — relational continuity."""

from __future__ import annotations

import json
from time import time
from typing import Any

from aethos_core.relational.paths import relational_root


def _path(session_id: str):
    return relational_root() / f"conversational_{session_id}.json"


def append_turn(*, session_id: str, role: str, summary: str) -> None:
    path = _path(session_id)
    rows: list[dict[str, Any]] = []
    if path.is_file():
        try:
            rows = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            rows = []
    rows.insert(0, {"at": time(), "role": role, "summary": summary[:200]})
    path.write_text(json.dumps(rows[:40], indent=2), encoding="utf-8")


def recent_context(*, session_id: str = "default", limit: int = 5) -> list[dict[str, Any]]:
    path = _path(session_id)
    if not path.is_file():
        return []
    try:
        return json.loads(path.read_text(encoding="utf-8"))[:limit]
    except (OSError, json.JSONDecodeError):
        return []

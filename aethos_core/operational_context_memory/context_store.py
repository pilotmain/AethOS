# SPDX-License-Identifier: Apache-2.0
"""Context store — deployment/replay/recovery continuity persistence."""

from __future__ import annotations

import json
from pathlib import Path
from time import time
from typing import Any


def _root() -> Path:
    root = Path(__file__).resolve().parents[2] / "data" / "conversation" / "operational_context"
    root.mkdir(parents=True, exist_ok=True)
    return root


def _path(session_id: str) -> Path:
    return _root() / f"context_{session_id}.json"


def recall_operational_context(*, session_id: str = "default") -> dict[str, Any]:
    path = _path(session_id)
    if not path.is_file():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}


def persist_operational_context(*, session_id: str = "default", context: dict[str, Any]) -> dict[str, Any]:
    existing = recall_operational_context(session_id=session_id)
    merged = {**existing, **context, "updated_at": time()}
    _path(session_id).write_text(json.dumps(merged, indent=2), encoding="utf-8")
    return merged

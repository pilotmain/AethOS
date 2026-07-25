# SPDX-License-Identifier: Apache-2.0
"""Trust memory — safely remembers operator preferences."""

from __future__ import annotations

import json
from time import time
from typing import Any

from aethos_core.relational.paths import relational_root


def _path(session_id: str):
    return relational_root() / f"trust_memory_{session_id}.json"


def recall_trust_preferences(*, session_id: str = "default") -> dict[str, Any]:
    path = _path(session_id)
    if not path.is_file():
        return {"interruption_budget": 3, "prefers_brevity": False, "prefers_explanations": True}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}


def remember_preference(*, session_id: str = "default", key: str, value: Any) -> None:
    prefs = recall_trust_preferences(session_id=session_id)
    prefs[key] = value
    prefs["updated_at"] = time()
    _path(session_id).write_text(json.dumps(prefs, indent=2), encoding="utf-8")


def clear_trust_memory_for_tests() -> None:
    root = relational_root()
    for p in root.glob("trust_memory_*.json"):
        p.unlink()
    for p in root.glob("style_*.json"):
        p.unlink()
    for p in root.glob("conversational_*.json"):
        p.unlink()

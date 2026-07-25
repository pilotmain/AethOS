# SPDX-License-Identifier: Apache-2.0
"""Operator style — adaptive tone and personality preferences."""

from __future__ import annotations

import json
from typing import Any

from aethos_core.relational.paths import relational_root


def _path(session_id: str):
    return relational_root() / f"style_{session_id}.json"


def get_operator_style(*, session_id: str = "default") -> dict[str, Any]:
    path = _path(session_id)
    if not path.is_file():
        return {"preferred_mode": "companion", "verbosity": "medium", "formality": "balanced"}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {"preferred_mode": "companion", "verbosity": "medium"}


def set_operator_style(*, session_id: str = "default", preferred_mode: str = "companion", verbosity: str = "medium") -> dict[str, Any]:
    record = {"preferred_mode": preferred_mode, "verbosity": verbosity, "formality": "balanced"}
    _path(session_id).write_text(json.dumps(record, indent=2), encoding="utf-8")
    return record

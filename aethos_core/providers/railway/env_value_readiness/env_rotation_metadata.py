# SPDX-License-Identifier: Apache-2.0
"""Rotation metadata for env secrets — no vault reads, no secret inspection."""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any


def _rotation_store_path(target_key: str) -> Path:
    safe = re.sub(r"[^a-zA-Z0-9_|.-]+", "_", target_key)[:180]
    root = Path(__file__).resolve().parents[3] / "data" / "railway_env_rotation_metadata"
    root.mkdir(parents=True, exist_ok=True)
    return root / f"{safe}.json"


def load_rotation_metadata(target_key: str) -> dict[str, dict[str, Any]]:
    path = _rotation_store_path(target_key)
    if not path.is_file():
        return {}
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}
    hints = raw.get("env_vars") if isinstance(raw, dict) else {}
    return dict(hints) if isinstance(hints, dict) else {}


def attach_rotation_metadata(
    name: str,
    entry: dict[str, Any],
    *,
    target_key: str,
) -> dict[str, Any]:
    enriched = dict(entry)
    hints = load_rotation_metadata(target_key)
    row = hints.get(name.upper()) or hints.get(name) or {}
    rotation_state = str(row.get("rotation_state") or "unknown").lower()
    if rotation_state not in {"healthy", "aging", "expired", "unknown"}:
        rotation_state = "unknown"
    enriched["rotation_state"] = rotation_state
    days = row.get("last_updated_days")
    enriched["last_updated_days"] = int(days) if days is not None else None
    return enriched


def clear_rotation_metadata_for_tests() -> None:
    root = Path(__file__).resolve().parents[3] / "data" / "railway_env_rotation_metadata"
    if root.is_dir():
        for path in root.glob("*.json"):
            path.unlink()


def set_rotation_metadata_for_tests(
    *,
    target_key: str,
    env_vars: dict[str, dict[str, Any]],
) -> None:
    path = _rotation_store_path(target_key)
    path.write_text(json.dumps({"env_vars": env_vars}, indent=2), encoding="utf-8")

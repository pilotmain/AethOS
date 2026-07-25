# SPDX-License-Identifier: Apache-2.0
"""FIX 316B — identity truth lock review store."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from aethos_core.identity_truth_lock.identity_truth_lock_contract import (
    IDENTITY_REVIEW_RECORD_KINDS,
    IDENTITY_REVIEW_RECORD_SCHEMA_VERSION,
    MAX_IDENTITY_REVIEW_CONTENT_LEN,
    MAX_PERSISTED_IDENTITY_REVIEW_RECORDS,
)

_DEFAULT_STORE = Path("data/identity_truth_lock/review_records.json")


def _utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def _store_path() -> Path:
    return Path(
        __import__("os").environ.get(
            "AETHOS_IDENTITY_TRUTH_LOCK_STORE",
            str(_DEFAULT_STORE),
        )
    )


def _load_raw() -> dict[str, Any]:
    path = _store_path()
    if not path.exists():
        return {"records": []}
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return {"records": []}
    if not isinstance(payload, dict):
        return {"records": []}
    records = payload.get("records")
    if not isinstance(records, list):
        payload["records"] = []
    return payload


def _save_raw(payload: dict[str, Any]) -> None:
    path = _store_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")


def list_identity_review_records() -> list[dict[str, Any]]:
    return list(_load_raw().get("records") or [])


def clear_identity_review_records_for_tests() -> None:
    path = _store_path()
    if path.exists():
        path.unlink(missing_ok=True)


def append_identity_review_record(
    *,
    kind: str,
    content: str,
    session_id: str | None = None,
) -> dict[str, Any]:
    if kind not in IDENTITY_REVIEW_RECORD_KINDS:
        raise ValueError(f"unsupported identity review kind: {kind}")

    trimmed = (content or "").strip()
    if not trimmed:
        raise ValueError("identity review content required")
    if len(trimmed) > MAX_IDENTITY_REVIEW_CONTENT_LEN:
        trimmed = trimmed[:MAX_IDENTITY_REVIEW_CONTENT_LEN]

    record = {
        "schema_version": IDENTITY_REVIEW_RECORD_SCHEMA_VERSION,
        "kind": kind,
        "content": trimmed,
        "session_id": (session_id or "").strip()[:64] or None,
        "recorded_at": _utc_now(),
    }

    payload = _load_raw()
    records = list(payload.get("records") or [])
    records.append(record)
    payload["records"] = records[-MAX_PERSISTED_IDENTITY_REVIEW_RECORDS:]
    _save_raw(payload)
    return record

# SPDX-License-Identifier: Apache-2.0
"""FIX 358 / WORKSTREAM_H1 — strategic direction & next-growth decision store."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from aethos_core.workstreams.strategic_direction_next_growth_decision_program.strategic_direction_next_growth_decision_program_contract import (
    MAX_PERSISTED_STRATEGIC_DIRECTION_RECORDS,
    MAX_STRATEGIC_DIRECTION_CONTENT_LEN,
    STRATEGIC_DIRECTION_NEXT_GROWTH_DECISION_PROGRAM_RECORD_SCHEMA_VERSION,
    STRATEGIC_DIRECTION_RECORD_KINDS,
)

_DEFAULT_STORE = Path("data/workstream_h1_strategic_direction_next_growth/records.json")


def _utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def _store_path() -> Path:
    return Path(
        __import__("os").environ.get(
            "AETHOS_WORKSTREAM_H1_STORE",
            str(_DEFAULT_STORE),
        )
    )


def _load_raw() -> dict[str, Any]:
    empty: dict[str, Any] = {"records": []}
    path = _store_path()
    if not path.exists():
        return empty
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return empty
    if not isinstance(payload, dict):
        return empty
    if not isinstance(payload.get("records"), list):
        payload["records"] = []
    return payload


def _save_raw(payload: dict[str, Any]) -> None:
    path = _store_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")


def clear_strategic_direction_records_for_tests() -> None:
    path = _store_path()
    if path.exists():
        path.unlink(missing_ok=True)


def list_strategic_direction_records() -> list[dict[str, Any]]:
    return list(_load_raw().get("records") or [])


def has_strategic_direction_review_approve(*, program_session_id: str | None = None) -> bool:
    for record in list_strategic_direction_records():
        if program_session_id and str(record.get("session_id") or "") != program_session_id:
            continue
        if str(record.get("kind") or "") == "strategic_direction_review_approve":
            return True
    return False


def append_strategic_direction_record(
    *,
    kind: str,
    content: str,
    session_id: str | None = None,
    metadata: dict[str, Any] | None = None,
) -> dict[str, Any]:
    normalized_kind = str(kind or "").strip()
    if normalized_kind not in STRATEGIC_DIRECTION_RECORD_KINDS:
        raise ValueError(f"unsupported strategic direction record kind: {kind!r}")

    normalized_content = str(content or "").strip()
    if not normalized_content:
        raise ValueError("content is required")
    if len(normalized_content) > MAX_STRATEGIC_DIRECTION_CONTENT_LEN:
        raise ValueError("content exceeds maximum length")

    payload = _load_raw()
    records = list(payload.get("records") or [])
    record = {
        "schema_version": STRATEGIC_DIRECTION_NEXT_GROWTH_DECISION_PROGRAM_RECORD_SCHEMA_VERSION,
        "record_id": f"h1-{len(records) + 1:05d}",
        "kind": normalized_kind,
        "content": normalized_content,
        "session_id": (session_id or "default").strip()[:64] or "default",
        "metadata": dict(metadata or {}),
        "recorded_at": _utc_now(),
    }
    records.append(record)
    if len(records) > MAX_PERSISTED_STRATEGIC_DIRECTION_RECORDS:
        records = records[-MAX_PERSISTED_STRATEGIC_DIRECTION_RECORDS:]
    payload["records"] = records
    _save_raw(payload)
    return record

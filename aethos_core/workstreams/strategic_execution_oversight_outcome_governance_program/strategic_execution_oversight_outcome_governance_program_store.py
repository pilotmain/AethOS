# SPDX-License-Identifier: Apache-2.0
"""FIX 360 / WORKSTREAM_H3 — strategic execution oversight store."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from aethos_core.workstreams.strategic_execution_oversight_outcome_governance_program.strategic_execution_oversight_outcome_governance_program_contract import (
    MAX_PERSISTED_STRATEGIC_OVERSIGHT_RECORDS,
    MAX_STRATEGIC_OVERSIGHT_CONTENT_LEN,
    STRATEGIC_EXECUTION_OVERSIGHT_OUTCOME_GOVERNANCE_PROGRAM_RECORD_SCHEMA_VERSION,
    STRATEGIC_OVERSIGHT_RECORD_KINDS,
)

_DEFAULT_STORE = Path("data/workstream_h3_strategic_execution_oversight/records.json")


def _utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def _store_path() -> Path:
    return Path(
        __import__("os").environ.get(
            "AETHOS_WORKSTREAM_H3_STORE",
            str(_DEFAULT_STORE),
        )
    )


def _load_raw() -> dict[str, Any]:
    empty: dict[str, Any] = {
        "records": [],
        "oversight_milestone_registry": [],
        "initiative_status_registry": [],
    }
    path = _store_path()
    if not path.exists():
        return empty
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return empty
    if not isinstance(payload, dict):
        return empty
    for key in empty:
        if not isinstance(payload.get(key), list):
            payload[key] = []
    return payload


def _save_raw(payload: dict[str, Any]) -> None:
    path = _store_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")


def clear_strategic_oversight_records_for_tests() -> None:
    path = _store_path()
    if path.exists():
        path.unlink(missing_ok=True)


def list_strategic_oversight_records() -> list[dict[str, Any]]:
    return list(_load_raw().get("records") or [])


def list_oversight_milestone_registry_entries() -> list[dict[str, Any]]:
    return list(_load_raw().get("oversight_milestone_registry") or [])


def list_initiative_status_registry_entries() -> list[dict[str, Any]]:
    return list(_load_raw().get("initiative_status_registry") or [])


def has_strategic_oversight_review_approve(*, program_session_id: str | None = None) -> bool:
    for record in list_strategic_oversight_records():
        if program_session_id and str(record.get("session_id") or "") != program_session_id:
            continue
        if str(record.get("kind") or "") == "strategic_oversight_review_approve":
            return True
    return False


def register_oversight_milestone(*, entry: dict[str, Any]) -> dict[str, Any]:
    payload = _load_raw()
    registry = list(payload.get("oversight_milestone_registry") or [])
    normalized = dict(entry)
    normalized.setdefault("registered_at", _utc_now())
    milestone_key = (
        f"{normalized.get('initiative_id')}:{normalized.get('milestone')}"
    )
    for idx, row in enumerate(registry):
        existing_key = f"{row.get('initiative_id')}:{row.get('milestone')}"
        if existing_key == milestone_key and milestone_key != ":":
            registry[idx] = normalized
            payload["oversight_milestone_registry"] = registry
            _save_raw(payload)
            return normalized
    registry.append(normalized)
    payload["oversight_milestone_registry"] = registry
    _save_raw(payload)
    return normalized


def register_initiative_status(*, entry: dict[str, Any]) -> dict[str, Any]:
    payload = _load_raw()
    registry = list(payload.get("initiative_status_registry") or [])
    normalized = dict(entry)
    normalized.setdefault("registered_at", _utc_now())
    initiative_id = str(normalized.get("initiative_id") or "")
    for idx, row in enumerate(registry):
        if str(row.get("initiative_id") or "") == initiative_id and initiative_id:
            registry[idx] = normalized
            payload["initiative_status_registry"] = registry
            _save_raw(payload)
            return normalized
    registry.append(normalized)
    payload["initiative_status_registry"] = registry
    _save_raw(payload)
    return normalized


def append_strategic_oversight_record(
    *,
    kind: str,
    content: str,
    session_id: str | None = None,
    metadata: dict[str, Any] | None = None,
) -> dict[str, Any]:
    normalized_kind = str(kind or "").strip()
    if normalized_kind not in STRATEGIC_OVERSIGHT_RECORD_KINDS:
        raise ValueError(f"unsupported strategic oversight record kind: {kind!r}")

    normalized_content = str(content or "").strip()
    if not normalized_content:
        raise ValueError("content is required")
    if len(normalized_content) > MAX_STRATEGIC_OVERSIGHT_CONTENT_LEN:
        raise ValueError("content exceeds maximum length")

    payload = _load_raw()
    records = list(payload.get("records") or [])
    record = {
        "schema_version": STRATEGIC_EXECUTION_OVERSIGHT_OUTCOME_GOVERNANCE_PROGRAM_RECORD_SCHEMA_VERSION,
        "record_id": f"h3-{len(records) + 1:05d}",
        "kind": normalized_kind,
        "content": normalized_content,
        "session_id": (session_id or "default").strip()[:64] or "default",
        "metadata": dict(metadata or {}),
        "recorded_at": _utc_now(),
    }
    records.append(record)
    if len(records) > MAX_PERSISTED_STRATEGIC_OVERSIGHT_RECORDS:
        records = records[-MAX_PERSISTED_STRATEGIC_OVERSIGHT_RECORDS:]
    payload["records"] = records
    _save_raw(payload)
    return record

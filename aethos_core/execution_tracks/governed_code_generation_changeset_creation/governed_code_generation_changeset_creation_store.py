# SPDX-License-Identifier: Apache-2.0
"""FIX 335 — governed code generation and changeset creation store."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from aethos_core.execution_tracks.governed_code_generation_changeset_creation.governed_code_generation_changeset_creation_contract import (
    GOVERNED_CODE_GENERATION_CHANGESET_CREATION_RECORD_SCHEMA_VERSION,
    GOVERNED_CODE_GENERATION_RECORD_KINDS,
    MAX_GOVERNED_CODE_GENERATION_CONTENT_LEN,
    MAX_PERSISTED_GOVERNED_CODE_GENERATION_RECORDS,
)

_DEFAULT_STORE = Path("data/execution_track_2_governed_code_generation/records.json")


def _utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def _store_path() -> Path:
    return Path(
        __import__("os").environ.get(
            "AETHOS_EXECUTION_TRACK_2_STORE",
            str(_DEFAULT_STORE),
        )
    )


def _load_raw() -> dict[str, Any]:
    path = _store_path()
    if not path.exists():
        return {"records": [], "changeset_registry": []}
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return {"records": [], "changeset_registry": []}
    if not isinstance(payload, dict):
        return {"records": [], "changeset_registry": []}
    if not isinstance(payload.get("records"), list):
        payload["records"] = []
    if not isinstance(payload.get("changeset_registry"), list):
        payload["changeset_registry"] = []
    return payload


def _save_raw(payload: dict[str, Any]) -> None:
    path = _store_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")


def list_governed_code_generation_records() -> list[dict[str, Any]]:
    return list(_load_raw().get("records") or [])


def list_changeset_registry_entries() -> list[dict[str, Any]]:
    return list(_load_raw().get("changeset_registry") or [])


def clear_governed_code_generation_records_for_tests() -> None:
    path = _store_path()
    if path.exists():
        path.unlink(missing_ok=True)


def has_generation_decision_approve(*, session_id: str | None = None) -> bool:
    for record in list_governed_code_generation_records():
        if session_id and str(record.get("session_id") or "") != session_id:
            continue
        if str(record.get("kind") or "") == "generation_decision_approve":
            return True
    return False


def has_code_generation_executed(*, session_id: str | None = None) -> bool:
    for record in list_governed_code_generation_records():
        if session_id and str(record.get("session_id") or "") != session_id:
            continue
        if str(record.get("kind") or "") == "code_generation_executed_note":
            return True
    return False


def latest_record_by_kind(*, session_id: str, kind: str) -> dict[str, Any] | None:
    matches = [
        row
        for row in list_governed_code_generation_records()
        if str(row.get("kind") or "") == kind
        and str(row.get("session_id") or session_id) == session_id
    ]
    return matches[-1] if matches else None


def append_governed_code_generation_record(
    *,
    kind: str,
    content: str,
    session_id: str | None = None,
    metadata: dict[str, Any] | None = None,
) -> dict[str, Any]:
    normalized_kind = str(kind or "").strip()
    if normalized_kind not in GOVERNED_CODE_GENERATION_RECORD_KINDS:
        raise ValueError(f"unsupported governed code generation record kind: {kind!r}")

    normalized_content = str(content or "").strip()
    if not normalized_content:
        raise ValueError("content is required")
    if len(normalized_content) > MAX_GOVERNED_CODE_GENERATION_CONTENT_LEN:
        raise ValueError("content exceeds maximum length")

    payload = _load_raw()
    records = list(payload.get("records") or [])
    record = {
        "schema_version": GOVERNED_CODE_GENERATION_CHANGESET_CREATION_RECORD_SCHEMA_VERSION,
        "record_id": f"et2-{len(records) + 1:05d}",
        "kind": normalized_kind,
        "content": normalized_content,
        "session_id": (session_id or "default").strip()[:64] or "default",
        "metadata": dict(metadata or {}),
        "recorded_at": _utc_now(),
    }
    records.append(record)
    if len(records) > MAX_PERSISTED_GOVERNED_CODE_GENERATION_RECORDS:
        records = records[-MAX_PERSISTED_GOVERNED_CODE_GENERATION_RECORDS:]
    payload["records"] = records
    _save_raw(payload)
    return record


def register_changeset_entry(*, entry: dict[str, Any]) -> dict[str, Any]:
    payload = _load_raw()
    registry = list(payload.get("changeset_registry") or [])
    normalized = dict(entry)
    normalized.setdefault("registered_at", _utc_now())
    existing_idx = None
    for idx, row in enumerate(registry):
        if str(row.get("changeset_id") or "") == str(normalized.get("changeset_id") or ""):
            existing_idx = idx
            break
    if existing_idx is not None:
        registry[existing_idx] = normalized
    else:
        registry.append(normalized)
    payload["changeset_registry"] = registry
    _save_raw(payload)
    return normalized

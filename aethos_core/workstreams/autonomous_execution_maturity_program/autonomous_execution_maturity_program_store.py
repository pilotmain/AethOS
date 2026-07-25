# SPDX-License-Identifier: Apache-2.0
"""FIX 361 / PHASE_I1 — autonomous execution maturity store."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from aethos_core.workstreams.autonomous_execution_maturity_program.autonomous_execution_maturity_program_contract import (
    AUTONOMOUS_EXECUTION_MATURITY_PROGRAM_RECORD_SCHEMA_VERSION,
    AUTONOMOUS_EXECUTION_RECORD_KINDS,
    MAX_AUTONOMOUS_EXECUTION_CONTENT_LEN,
    MAX_PERSISTED_AUTONOMOUS_EXECUTION_RECORDS,
)

_DEFAULT_STORE = Path("data/phase_i1_autonomous_execution_maturity/records.json")


def _utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def _store_path() -> Path:
    return Path(
        __import__("os").environ.get(
            "AETHOS_PHASE_I1_STORE",
            str(_DEFAULT_STORE),
        )
    )


def _load_raw() -> dict[str, Any]:
    empty: dict[str, Any] = {"records": [], "autonomous_execution_registry": []}
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


def clear_autonomous_execution_records_for_tests() -> None:
    path = _store_path()
    if path.exists():
        path.unlink(missing_ok=True)


def list_autonomous_execution_records() -> list[dict[str, Any]]:
    return list(_load_raw().get("records") or [])


def list_autonomous_execution_registry_entries() -> list[dict[str, Any]]:
    return list(_load_raw().get("autonomous_execution_registry") or [])


def has_autonomous_execution_review_approve(*, program_session_id: str | None = None) -> bool:
    for record in list_autonomous_execution_records():
        if program_session_id and str(record.get("session_id") or "") != program_session_id:
            continue
        if str(record.get("kind") or "") == "autonomous_execution_review_approve":
            return True
    return False


def register_autonomous_execution_request(*, entry: dict[str, Any]) -> dict[str, Any]:
    payload = _load_raw()
    registry = list(payload.get("autonomous_execution_registry") or [])
    normalized = dict(entry)
    normalized.setdefault("registered_at", _utc_now())
    request_id = str(normalized.get("request_id") or "")
    for idx, row in enumerate(registry):
        if str(row.get("request_id") or "") == request_id and request_id:
            registry[idx] = normalized
            payload["autonomous_execution_registry"] = registry
            _save_raw(payload)
            return normalized
    registry.append(normalized)
    payload["autonomous_execution_registry"] = registry
    _save_raw(payload)
    return normalized


def append_autonomous_execution_record(
    *,
    kind: str,
    content: str,
    session_id: str | None = None,
    metadata: dict[str, Any] | None = None,
) -> dict[str, Any]:
    normalized_kind = str(kind or "").strip()
    if normalized_kind not in AUTONOMOUS_EXECUTION_RECORD_KINDS:
        raise ValueError(f"unsupported autonomous execution record kind: {kind!r}")

    normalized_content = str(content or "").strip()
    if not normalized_content:
        raise ValueError("content is required")
    if len(normalized_content) > MAX_AUTONOMOUS_EXECUTION_CONTENT_LEN:
        raise ValueError("content exceeds maximum length")

    payload = _load_raw()
    records = list(payload.get("records") or [])
    record = {
        "schema_version": AUTONOMOUS_EXECUTION_MATURITY_PROGRAM_RECORD_SCHEMA_VERSION,
        "record_id": f"i1-{len(records) + 1:05d}",
        "kind": normalized_kind,
        "content": normalized_content,
        "session_id": (session_id or "default").strip()[:64] or "default",
        "metadata": dict(metadata or {}),
        "recorded_at": _utc_now(),
    }
    records.append(record)
    if len(records) > MAX_PERSISTED_AUTONOMOUS_EXECUTION_RECORDS:
        records = records[-MAX_PERSISTED_AUTONOMOUS_EXECUTION_RECORDS:]
    payload["records"] = records
    _save_raw(payload)
    return record

# SPDX-License-Identifier: Apache-2.0
"""FIX 366 / PHASE_J3 — compounding value continuous improvement store."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from aethos_core.workstreams.compounding_value_continuous_improvement_program.compounding_value_continuous_improvement_program_contract import (
    COMPOUNDING_VALUE_CONTINUOUS_IMPROVEMENT_PROGRAM_RECORD_SCHEMA_VERSION,
    CONTINUOUS_IMPROVEMENT_RECORD_KINDS,
    MAX_CONTINUOUS_IMPROVEMENT_CONTENT_LEN,
    MAX_PERSISTED_CONTINUOUS_IMPROVEMENT_RECORDS,
)

_DEFAULT_STORE = Path("data/phase_j3_compounding_value_continuous_improvement/records.json")


def _utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def _store_path() -> Path:
    return Path(
        __import__("os").environ.get(
            "AETHOS_PHASE_J3_STORE",
            str(_DEFAULT_STORE),
        )
    )


def _load_raw() -> dict[str, Any]:
    empty: dict[str, Any] = {"records": [], "improvement_baseline_registry": []}
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


def clear_continuous_improvement_records_for_tests() -> None:
    path = _store_path()
    if path.exists():
        path.unlink(missing_ok=True)


def list_continuous_improvement_records() -> list[dict[str, Any]]:
    return list(_load_raw().get("records") or [])


def list_improvement_baseline_registry_entries() -> list[dict[str, Any]]:
    return list(_load_raw().get("improvement_baseline_registry") or [])


def has_continuous_improvement_review_approve(*, program_session_id: str | None = None) -> bool:
    for record in list_continuous_improvement_records():
        if program_session_id and str(record.get("session_id") or "") != program_session_id:
            continue
        if str(record.get("kind") or "") == "continuous_improvement_review_approve":
            return True
    return False


def register_improvement_baseline(*, entry: dict[str, Any]) -> dict[str, Any]:
    payload = _load_raw()
    registry = list(payload.get("improvement_baseline_registry") or [])
    normalized = dict(entry)
    normalized.setdefault("registered_at", _utc_now())
    baseline_id = str(normalized.get("baseline_id") or "")
    for idx, row in enumerate(registry):
        if str(row.get("baseline_id") or "") == baseline_id and baseline_id:
            registry[idx] = normalized
            payload["improvement_baseline_registry"] = registry
            _save_raw(payload)
            return normalized
    registry.append(normalized)
    payload["improvement_baseline_registry"] = registry
    _save_raw(payload)
    return normalized


def append_continuous_improvement_record(
    *,
    kind: str,
    content: str,
    session_id: str | None = None,
    metadata: dict[str, Any] | None = None,
) -> dict[str, Any]:
    normalized_kind = str(kind or "").strip()
    if normalized_kind not in CONTINUOUS_IMPROVEMENT_RECORD_KINDS:
        raise ValueError(f"unsupported continuous improvement record kind: {kind!r}")

    normalized_content = str(content or "").strip()
    if not normalized_content:
        raise ValueError("content is required")
    if len(normalized_content) > MAX_CONTINUOUS_IMPROVEMENT_CONTENT_LEN:
        raise ValueError("content exceeds maximum length")

    payload = _load_raw()
    records = list(payload.get("records") or [])
    record = {
        "schema_version": COMPOUNDING_VALUE_CONTINUOUS_IMPROVEMENT_PROGRAM_RECORD_SCHEMA_VERSION,
        "record_id": f"j3-{len(records) + 1:05d}",
        "kind": normalized_kind,
        "content": normalized_content,
        "session_id": (session_id or "default").strip()[:64] or "default",
        "metadata": dict(metadata or {}),
        "recorded_at": _utc_now(),
    }
    records.append(record)
    if len(records) > MAX_PERSISTED_CONTINUOUS_IMPROVEMENT_RECORDS:
        records = records[-MAX_PERSISTED_CONTINUOUS_IMPROVEMENT_RECORDS:]
    payload["records"] = records
    _save_raw(payload)
    return record

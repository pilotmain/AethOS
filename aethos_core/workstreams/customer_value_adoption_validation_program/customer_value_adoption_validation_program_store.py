# SPDX-License-Identifier: Apache-2.0
"""FIX 348 / WORKSTREAM_F2 — customer value & adoption validation store."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from aethos_core.workstreams.customer_value_adoption_validation_program.customer_value_adoption_validation_program_contract import (
    CUSTOMER_VALUE_ADOPTION_VALIDATION_PROGRAM_RECORD_SCHEMA_VERSION,
    CUSTOMER_VALUE_ADOPTION_VALIDATION_RECORD_KINDS,
    MAX_CUSTOMER_VALUE_ADOPTION_VALIDATION_CONTENT_LEN,
    MAX_PERSISTED_CUSTOMER_VALUE_ADOPTION_VALIDATION_RECORDS,
)

_DEFAULT_STORE = Path("data/workstream_f2_customer_value_adoption_validation/records.json")


def _utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def _store_path() -> Path:
    return Path(
        __import__("os").environ.get(
            "AETHOS_WORKSTREAM_F2_STORE",
            str(_DEFAULT_STORE),
        )
    )


def _load_raw() -> dict[str, Any]:
    empty: dict[str, Any] = {
        "records": [],
        "usage_observation_registry": [],
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


def clear_customer_value_adoption_validation_records_for_tests() -> None:
    path = _store_path()
    if path.exists():
        path.unlink(missing_ok=True)


def list_customer_value_adoption_validation_records() -> list[dict[str, Any]]:
    return list(_load_raw().get("records") or [])


def list_usage_observation_registry_entries() -> list[dict[str, Any]]:
    return list(_load_raw().get("usage_observation_registry") or [])


def has_customer_value_review_approve(*, session_id: str | None = None) -> bool:
    for record in list_customer_value_adoption_validation_records():
        if session_id and str(record.get("session_id") or "") != session_id:
            continue
        if str(record.get("kind") or "") == "customer_value_review_approve":
            return True
    return False


def register_usage_observation(*, entry: dict[str, Any]) -> dict[str, Any]:
    payload = _load_raw()
    registry = list(payload.get("usage_observation_registry") or [])
    normalized = dict(entry)
    normalized.setdefault("observed_at", _utc_now())
    registry.append(normalized)
    payload["usage_observation_registry"] = registry
    _save_raw(payload)
    return normalized


def append_customer_value_adoption_validation_record(
    *,
    kind: str,
    content: str,
    session_id: str | None = None,
    metadata: dict[str, Any] | None = None,
) -> dict[str, Any]:
    normalized_kind = str(kind or "").strip()
    if normalized_kind not in CUSTOMER_VALUE_ADOPTION_VALIDATION_RECORD_KINDS:
        raise ValueError(f"unsupported validation record kind: {kind!r}")

    normalized_content = str(content or "").strip()
    if not normalized_content:
        raise ValueError("content is required")
    if len(normalized_content) > MAX_CUSTOMER_VALUE_ADOPTION_VALIDATION_CONTENT_LEN:
        raise ValueError("content exceeds maximum length")

    payload = _load_raw()
    records = list(payload.get("records") or [])
    record = {
        "schema_version": CUSTOMER_VALUE_ADOPTION_VALIDATION_PROGRAM_RECORD_SCHEMA_VERSION,
        "record_id": f"f2-{len(records) + 1:05d}",
        "kind": normalized_kind,
        "content": normalized_content,
        "session_id": (session_id or "default").strip()[:64] or "default",
        "metadata": dict(metadata or {}),
        "recorded_at": _utc_now(),
    }
    records.append(record)
    if len(records) > MAX_PERSISTED_CUSTOMER_VALUE_ADOPTION_VALIDATION_RECORDS:
        records = records[-MAX_PERSISTED_CUSTOMER_VALUE_ADOPTION_VALIDATION_RECORDS:]
    payload["records"] = records
    _save_raw(payload)
    return record

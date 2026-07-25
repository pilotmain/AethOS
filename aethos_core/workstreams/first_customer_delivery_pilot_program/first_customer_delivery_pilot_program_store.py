# SPDX-License-Identifier: Apache-2.0
"""FIX 347 / WORKSTREAM_F1 — first customer delivery pilot store."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from aethos_core.workstreams.first_customer_delivery_pilot_program.first_customer_delivery_pilot_program_contract import (
    FIRST_CUSTOMER_DELIVERY_PILOT_PROGRAM_RECORD_SCHEMA_VERSION,
    FIRST_CUSTOMER_DELIVERY_PILOT_RECORD_KINDS,
    MAX_FIRST_CUSTOMER_DELIVERY_PILOT_CONTENT_LEN,
    MAX_PERSISTED_FIRST_CUSTOMER_DELIVERY_PILOT_RECORDS,
)

_DEFAULT_STORE = Path("data/workstream_f1_first_customer_delivery_pilot/records.json")


def _utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def _store_path() -> Path:
    return Path(
        __import__("os").environ.get(
            "AETHOS_WORKSTREAM_F1_STORE",
            str(_DEFAULT_STORE),
        )
    )


def _load_raw() -> dict[str, Any]:
    empty: dict[str, Any] = {
        "records": [],
        "customer_delivery_request_registry": [],
        "customer_pilot_run_registry": [],
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


def clear_first_customer_delivery_pilot_records_for_tests() -> None:
    path = _store_path()
    if path.exists():
        path.unlink(missing_ok=True)


def list_first_customer_delivery_pilot_records() -> list[dict[str, Any]]:
    return list(_load_raw().get("records") or [])


def list_customer_delivery_request_registry_entries() -> list[dict[str, Any]]:
    return list(_load_raw().get("customer_delivery_request_registry") or [])


def list_customer_pilot_run_registry_entries() -> list[dict[str, Any]]:
    return list(_load_raw().get("customer_pilot_run_registry") or [])


def has_customer_pilot_review_approve(*, session_id: str | None = None) -> bool:
    for record in list_first_customer_delivery_pilot_records():
        if session_id and str(record.get("session_id") or "") != session_id:
            continue
        if str(record.get("kind") or "") == "customer_pilot_review_approve":
            return True
    return False


def get_latest_customer_delivery_request(*, session_id: str) -> dict[str, Any] | None:
    entries = [
        row
        for row in list_customer_delivery_request_registry_entries()
        if str(row.get("session_id") or "") == session_id
    ]
    return entries[-1] if entries else None


def register_customer_delivery_request(*, entry: dict[str, Any]) -> dict[str, Any]:
    payload = _load_raw()
    registry = list(payload.get("customer_delivery_request_registry") or [])
    normalized = dict(entry)
    normalized.setdefault("registered_at", _utc_now())
    registry.append(normalized)
    payload["customer_delivery_request_registry"] = registry
    _save_raw(payload)
    return normalized


def register_customer_pilot_run(*, entry: dict[str, Any]) -> dict[str, Any]:
    payload = _load_raw()
    registry = list(payload.get("customer_pilot_run_registry") or [])
    normalized = dict(entry)
    normalized.setdefault("registered_at", _utc_now())
    registry.append(normalized)
    payload["customer_pilot_run_registry"] = registry
    _save_raw(payload)
    return normalized


def append_first_customer_delivery_pilot_record(
    *,
    kind: str,
    content: str,
    session_id: str | None = None,
    metadata: dict[str, Any] | None = None,
) -> dict[str, Any]:
    normalized_kind = str(kind or "").strip()
    if normalized_kind not in FIRST_CUSTOMER_DELIVERY_PILOT_RECORD_KINDS:
        raise ValueError(f"unsupported pilot record kind: {kind!r}")

    normalized_content = str(content or "").strip()
    if not normalized_content:
        raise ValueError("content is required")
    if len(normalized_content) > MAX_FIRST_CUSTOMER_DELIVERY_PILOT_CONTENT_LEN:
        raise ValueError("content exceeds maximum length")

    payload = _load_raw()
    records = list(payload.get("records") or [])
    record = {
        "schema_version": FIRST_CUSTOMER_DELIVERY_PILOT_PROGRAM_RECORD_SCHEMA_VERSION,
        "record_id": f"f1-{len(records) + 1:05d}",
        "kind": normalized_kind,
        "content": normalized_content,
        "session_id": (session_id or "default").strip()[:64] or "default",
        "metadata": dict(metadata or {}),
        "recorded_at": _utc_now(),
    }
    records.append(record)
    if len(records) > MAX_PERSISTED_FIRST_CUSTOMER_DELIVERY_PILOT_RECORDS:
        records = records[-MAX_PERSISTED_FIRST_CUSTOMER_DELIVERY_PILOT_RECORDS:]
    payload["records"] = records
    _save_raw(payload)
    return record

# SPDX-License-Identifier: Apache-2.0
"""FIX 355 / WORKSTREAM_G2 — real usage density & platform adoption store."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from aethos_core.workstreams.real_usage_density_platform_adoption_program.real_usage_density_platform_adoption_program_contract import (
    MAX_PERSISTED_PLATFORM_ADOPTION_RECORDS,
    MAX_PLATFORM_ADOPTION_CONTENT_LEN,
    PLATFORM_ADOPTION_RECORD_KINDS,
    REAL_USAGE_DENSITY_PLATFORM_ADOPTION_PROGRAM_RECORD_SCHEMA_VERSION,
)

_DEFAULT_STORE = Path("data/workstream_g2_real_usage_density_platform_adoption/records.json")


def _utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def _store_path() -> Path:
    return Path(
        __import__("os").environ.get(
            "AETHOS_WORKSTREAM_G2_STORE",
            str(_DEFAULT_STORE),
        )
    )


def _load_raw() -> dict[str, Any]:
    empty: dict[str, Any] = {"records": [], "usage_session_registry": []}
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


def clear_platform_adoption_records_for_tests() -> None:
    path = _store_path()
    if path.exists():
        path.unlink(missing_ok=True)


def list_platform_adoption_records() -> list[dict[str, Any]]:
    return list(_load_raw().get("records") or [])


def list_usage_session_registry_entries() -> list[dict[str, Any]]:
    return list(_load_raw().get("usage_session_registry") or [])


def has_platform_adoption_review_approve(*, program_session_id: str | None = None) -> bool:
    for record in list_platform_adoption_records():
        if program_session_id and str(record.get("session_id") or "") != program_session_id:
            continue
        if str(record.get("kind") or "") == "platform_adoption_review_approve":
            return True
    return False


def register_usage_session_entry(*, entry: dict[str, Any]) -> dict[str, Any]:
    payload = _load_raw()
    registry = list(payload.get("usage_session_registry") or [])
    normalized = dict(entry)
    normalized.setdefault("registered_at", _utc_now())
    session_key = str(normalized.get("usage_session_id") or normalized.get("customer_session_id") or "")
    for idx, row in enumerate(registry):
        if str(row.get("usage_session_id") or row.get("customer_session_id") or "") == session_key and session_key:
            registry[idx] = normalized
            payload["usage_session_registry"] = registry
            _save_raw(payload)
            return normalized
    registry.append(normalized)
    payload["usage_session_registry"] = registry
    _save_raw(payload)
    return normalized


def append_platform_adoption_record(
    *,
    kind: str,
    content: str,
    session_id: str | None = None,
    metadata: dict[str, Any] | None = None,
) -> dict[str, Any]:
    normalized_kind = str(kind or "").strip()
    if normalized_kind not in PLATFORM_ADOPTION_RECORD_KINDS:
        raise ValueError(f"unsupported platform adoption record kind: {kind!r}")

    normalized_content = str(content or "").strip()
    if not normalized_content:
        raise ValueError("content is required")
    if len(normalized_content) > MAX_PLATFORM_ADOPTION_CONTENT_LEN:
        raise ValueError("content exceeds maximum length")

    payload = _load_raw()
    records = list(payload.get("records") or [])
    record = {
        "schema_version": REAL_USAGE_DENSITY_PLATFORM_ADOPTION_PROGRAM_RECORD_SCHEMA_VERSION,
        "record_id": f"g2-{len(records) + 1:05d}",
        "kind": normalized_kind,
        "content": normalized_content,
        "session_id": (session_id or "default").strip()[:64] or "default",
        "metadata": dict(metadata or {}),
        "recorded_at": _utc_now(),
    }
    records.append(record)
    if len(records) > MAX_PERSISTED_PLATFORM_ADOPTION_RECORDS:
        records = records[-MAX_PERSISTED_PLATFORM_ADOPTION_RECORDS:]
    payload["records"] = records
    _save_raw(payload)
    return record

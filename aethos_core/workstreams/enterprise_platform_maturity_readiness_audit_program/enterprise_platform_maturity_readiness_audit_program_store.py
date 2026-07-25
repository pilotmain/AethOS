# SPDX-License-Identifier: Apache-2.0
"""FIX 357 / WORKSTREAM_G4 — enterprise platform maturity & readiness audit store."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from aethos_core.workstreams.enterprise_platform_maturity_readiness_audit_program.enterprise_platform_maturity_readiness_audit_program_contract import (
    MAX_PERSISTED_PLATFORM_MATURITY_RECORDS,
    MAX_PLATFORM_MATURITY_CONTENT_LEN,
    ENTERPRISE_PLATFORM_MATURITY_READINESS_AUDIT_PROGRAM_RECORD_SCHEMA_VERSION,
    PLATFORM_MATURITY_RECORD_KINDS,
)

_DEFAULT_STORE = Path("data/workstream_g4_enterprise_platform_maturity_readiness_audit/records.json")


def _utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def _store_path() -> Path:
    return Path(
        __import__("os").environ.get(
            "AETHOS_WORKSTREAM_G4_STORE",
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


def clear_platform_maturity_records_for_tests() -> None:
    path = _store_path()
    if path.exists():
        path.unlink(missing_ok=True)


def list_platform_maturity_records() -> list[dict[str, Any]]:
    return list(_load_raw().get("records") or [])


def has_platform_maturity_review_approve(*, program_session_id: str | None = None) -> bool:
    for record in list_platform_maturity_records():
        if program_session_id and str(record.get("session_id") or "") != program_session_id:
            continue
        if str(record.get("kind") or "") == "platform_maturity_review_approve":
            return True
    return False


def append_platform_maturity_record(
    *,
    kind: str,
    content: str,
    session_id: str | None = None,
    metadata: dict[str, Any] | None = None,
) -> dict[str, Any]:
    normalized_kind = str(kind or "").strip()
    if normalized_kind not in PLATFORM_MATURITY_RECORD_KINDS:
        raise ValueError(f"unsupported platform maturity record kind: {kind!r}")

    normalized_content = str(content or "").strip()
    if not normalized_content:
        raise ValueError("content is required")
    if len(normalized_content) > MAX_PLATFORM_MATURITY_CONTENT_LEN:
        raise ValueError("content exceeds maximum length")

    payload = _load_raw()
    records = list(payload.get("records") or [])
    record = {
        "schema_version": ENTERPRISE_PLATFORM_MATURITY_READINESS_AUDIT_PROGRAM_RECORD_SCHEMA_VERSION,
        "record_id": f"g4-{len(records) + 1:05d}",
        "kind": normalized_kind,
        "content": normalized_content,
        "session_id": (session_id or "default").strip()[:64] or "default",
        "metadata": dict(metadata or {}),
        "recorded_at": _utc_now(),
    }
    records.append(record)
    if len(records) > MAX_PERSISTED_PLATFORM_MATURITY_RECORDS:
        records = records[-MAX_PERSISTED_PLATFORM_MATURITY_RECORDS:]
    payload["records"] = records
    _save_raw(payload)
    return record

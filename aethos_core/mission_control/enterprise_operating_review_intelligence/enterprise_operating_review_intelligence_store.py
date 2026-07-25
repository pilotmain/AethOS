# SPDX-License-Identifier: Apache-2.0
"""FIX 329 — executive operating review store."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from aethos_core.mission_control.enterprise_operating_review_intelligence.enterprise_operating_review_intelligence_contract import (
    ENTERPRISE_OPERATING_REVIEW_INTELLIGENCE_RECORD_SCHEMA_VERSION,
    MAX_OPERATING_REVIEW_CONTENT_LEN,
    MAX_PERSISTED_OPERATING_REVIEW_RECORDS,
    OPERATING_REVIEW_RECORD_KINDS,
)


def _utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def _store_path() -> Path:
    return Path(
        __import__("os").environ.get(
            "AETHOS_ENTERPRISE_OPERATING_REVIEW_INTELLIGENCE_STORE",
            str(Path("data/mission_control_enterprise_operating_review_intelligence/review_records.json")),
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
    if not isinstance(payload.get("records"), list):
        payload["records"] = []
    return payload


def _save_raw(payload: dict[str, Any]) -> None:
    path = _store_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")


def list_operating_review_records() -> list[dict[str, Any]]:
    return list(_load_raw().get("records") or [])


def has_operating_review_decision_approve(*, session_id: str | None = None) -> bool:
    for record in list_operating_review_records():
        if session_id and str(record.get("session_id") or "") != session_id:
            continue
        if str(record.get("kind") or "") == "operating_review_decision_approve":
            return True
    return False


def clear_operating_review_records_for_tests() -> None:
    path = _store_path()
    if path.exists():
        path.unlink(missing_ok=True)


def append_operating_review_record(
    *,
    kind: str,
    content: str,
    session_id: str | None = None,
    domain: str | None = None,
) -> dict[str, Any]:
    if kind not in OPERATING_REVIEW_RECORD_KINDS:
        raise ValueError(f"unsupported operating review kind: {kind}")

    trimmed = (content or "").strip()
    if not trimmed:
        raise ValueError("operating review content required")
    if len(trimmed) > MAX_OPERATING_REVIEW_CONTENT_LEN:
        trimmed = trimmed[:MAX_OPERATING_REVIEW_CONTENT_LEN]

    record = {
        "schema_version": ENTERPRISE_OPERATING_REVIEW_INTELLIGENCE_RECORD_SCHEMA_VERSION,
        "kind": kind,
        "content": trimmed,
        "session_id": (session_id or "").strip()[:64] or None,
        "domain": (domain or "").strip()[:64] or None,
        "recorded_at": _utc_now(),
    }

    payload = _load_raw()
    records = list(payload.get("records") or [])
    records.append(record)
    payload["records"] = records[-MAX_PERSISTED_OPERATING_REVIEW_RECORDS:]
    _save_raw(payload)
    return record

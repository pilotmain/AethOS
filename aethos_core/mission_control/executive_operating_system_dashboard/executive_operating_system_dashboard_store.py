# SPDX-License-Identifier: Apache-2.0
"""FIX 330 — executive dashboard review store."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from aethos_core.mission_control.executive_operating_system_dashboard.executive_operating_system_dashboard_contract import (
    DASHBOARD_RECORD_KINDS,
    EXECUTIVE_OPERATING_SYSTEM_DASHBOARD_RECORD_SCHEMA_VERSION,
    MAX_DASHBOARD_CONTENT_LEN,
    MAX_PERSISTED_DASHBOARD_RECORDS,
)


def _utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def _store_path() -> Path:
    return Path(
        __import__("os").environ.get(
            "AETHOS_EXECUTIVE_OPERATING_SYSTEM_DASHBOARD_STORE",
            str(Path("data/mission_control_executive_operating_system_dashboard/review_records.json")),
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


def list_dashboard_review_records() -> list[dict[str, Any]]:
    return list(_load_raw().get("records") or [])


def has_dashboard_review_decision_approve(*, session_id: str | None = None) -> bool:
    for record in list_dashboard_review_records():
        if session_id and str(record.get("session_id") or "") != session_id:
            continue
        if str(record.get("kind") or "") == "dashboard_review_decision_approve":
            return True
    return False


def clear_dashboard_review_records_for_tests() -> None:
    path = _store_path()
    if path.exists():
        path.unlink(missing_ok=True)


def append_dashboard_review_record(
    *,
    kind: str,
    content: str,
    session_id: str | None = None,
    domain: str | None = None,
) -> dict[str, Any]:
    if kind not in DASHBOARD_RECORD_KINDS:
        raise ValueError(f"unsupported dashboard review kind: {kind}")

    trimmed = (content or "").strip()
    if not trimmed:
        raise ValueError("dashboard review content required")
    if len(trimmed) > MAX_DASHBOARD_CONTENT_LEN:
        trimmed = trimmed[:MAX_DASHBOARD_CONTENT_LEN]

    record = {
        "schema_version": EXECUTIVE_OPERATING_SYSTEM_DASHBOARD_RECORD_SCHEMA_VERSION,
        "kind": kind,
        "content": trimmed,
        "session_id": (session_id or "").strip()[:64] or None,
        "domain": (domain or "").strip()[:64] or None,
        "recorded_at": _utc_now(),
    }

    payload = _load_raw()
    records = list(payload.get("records") or [])
    records.append(record)
    payload["records"] = records[-MAX_PERSISTED_DASHBOARD_RECORDS:]
    _save_raw(payload)
    return record

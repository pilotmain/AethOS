# SPDX-License-Identifier: Apache-2.0
"""FIX 318 — analytics review store."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from aethos_core.mission_control.product_analytics_foundation.product_analytics_foundation_contract import (
    ANALYTICS_REVIEW_RECORD_KINDS,
    MAX_ANALYTICS_REVIEW_CONTENT_LEN,
    MAX_PERSISTED_ANALYTICS_REVIEW_RECORDS,
    PRODUCT_ANALYTICS_FOUNDATION_RECORD_SCHEMA_VERSION,
)

_DEFAULT_STORE = Path("data/mission_control_product_analytics_foundation/review_records.json")


def _utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def _store_path() -> Path:
    return Path(
        __import__("os").environ.get(
            "AETHOS_PRODUCT_ANALYTICS_FOUNDATION_STORE",
            str(_DEFAULT_STORE),
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


def list_analytics_review_records() -> list[dict[str, Any]]:
    return list(_load_raw().get("records") or [])


def has_analytics_review_decision_approve(*, session_id: str | None = None) -> bool:
    for record in list_analytics_review_records():
        if session_id and str(record.get("session_id") or "") != session_id:
            continue
        if str(record.get("kind") or "") == "analytics_review_decision_approve":
            return True
    return False


def clear_analytics_review_records_for_tests() -> None:
    path = _store_path()
    if path.exists():
        path.unlink(missing_ok=True)


def append_analytics_review_record(
    *,
    kind: str,
    content: str,
    session_id: str | None = None,
    domain: str | None = None,
) -> dict[str, Any]:
    if kind not in ANALYTICS_REVIEW_RECORD_KINDS:
        raise ValueError(f"unsupported analytics review kind: {kind}")

    trimmed = (content or "").strip()
    if not trimmed:
        raise ValueError("analytics review content required")
    if len(trimmed) > MAX_ANALYTICS_REVIEW_CONTENT_LEN:
        trimmed = trimmed[:MAX_ANALYTICS_REVIEW_CONTENT_LEN]

    record = {
        "schema_version": PRODUCT_ANALYTICS_FOUNDATION_RECORD_SCHEMA_VERSION,
        "kind": kind,
        "content": trimmed,
        "session_id": (session_id or "").strip()[:64] or None,
        "domain": (domain or "").strip()[:64] or None,
        "recorded_at": _utc_now(),
    }

    payload = _load_raw()
    records = list(payload.get("records") or [])
    records.append(record)
    payload["records"] = records[-MAX_PERSISTED_ANALYTICS_REVIEW_RECORDS:]
    _save_raw(payload)
    return record

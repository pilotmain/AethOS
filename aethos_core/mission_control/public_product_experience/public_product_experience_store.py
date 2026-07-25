# SPDX-License-Identifier: Apache-2.0
"""FIX 311 — public product experience store."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from aethos_core.mission_control.public_product_experience.public_product_experience_contract import (
    HUMAN_PUBLIC_EXPERIENCE_DECISION_KINDS,
    MAX_PERSISTED_PUBLIC_PRODUCT_EXPERIENCE_RECORDS,
    MAX_PUBLIC_PRODUCT_EXPERIENCE_CONTENT_LEN,
    PUBLIC_PRODUCT_EXPERIENCE_RECORD_KINDS,
    PUBLIC_PRODUCT_EXPERIENCE_RECORD_SCHEMA_VERSION,
)

_DEFAULT_STORE = Path("data/mission_control_public_product_experience/records.json")


def _utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def _store_path() -> Path:
    return Path(
        __import__("os").environ.get(
            "AETHOS_PUBLIC_PRODUCT_EXPERIENCE_STORE",
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
    records = payload.get("records")
    if not isinstance(records, list):
        payload["records"] = []
    return payload


def _save_raw(payload: dict[str, Any]) -> None:
    path = _store_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")


def list_public_product_experience_records() -> list[dict[str, Any]]:
    return list(_load_raw().get("records") or [])


def clear_public_product_experience_records_for_tests() -> None:
    path = _store_path()
    if path.exists():
        path.unlink(missing_ok=True)


def has_public_experience_review_decision_approve(*, session_id: str | None = None) -> bool:
    for record in list_public_product_experience_records():
        if session_id and str(record.get("session_id") or "") != session_id:
            continue
        if str(record.get("kind") or "") == "public_experience_review_decision_approve":
            return True
    return False


def append_public_product_experience_record(
    *,
    kind: str,
    content: str,
    session_id: str | None = None,
    domain: str | None = None,
) -> dict[str, Any]:
    normalized_kind = str(kind or "").strip()
    if normalized_kind not in PUBLIC_PRODUCT_EXPERIENCE_RECORD_KINDS:
        raise ValueError(f"unsupported public product experience record kind: {kind!r}")

    normalized_content = str(content or "").strip()
    if not normalized_content:
        raise ValueError("content is required")
    if len(normalized_content) > MAX_PUBLIC_PRODUCT_EXPERIENCE_CONTENT_LEN:
        raise ValueError("content exceeds maximum length")

    record: dict[str, Any] = {
        "schema_version": PUBLIC_PRODUCT_EXPERIENCE_RECORD_SCHEMA_VERSION,
        "kind": normalized_kind,
        "content": normalized_content,
        "recorded_at": _utc_now(),
    }
    if session_id:
        record["session_id"] = str(session_id).strip()
    if domain:
        record["domain"] = str(domain).strip()
    if normalized_kind in HUMAN_PUBLIC_EXPERIENCE_DECISION_KINDS:
        record["public_experience_review_decision"] = normalized_kind.replace(
            "public_experience_review_decision_", ""
        )

    payload = _load_raw()
    records = list(payload.get("records") or [])
    records.append(record)
    payload["records"] = records[-MAX_PERSISTED_PUBLIC_PRODUCT_EXPERIENCE_RECORDS:]
    _save_raw(payload)
    return record

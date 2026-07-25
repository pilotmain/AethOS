# SPDX-License-Identifier: Apache-2.0
"""FIX 338 — end-to-end delivery certification store."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from aethos_core.execution_tracks.governed_end_to_end_delivery_certification.governed_end_to_end_delivery_certification_contract import (
    GOVERNED_END_TO_END_DELIVERY_CERTIFICATION_RECORD_KINDS,
    GOVERNED_END_TO_END_DELIVERY_CERTIFICATION_RECORD_SCHEMA_VERSION,
    MAX_GOVERNED_END_TO_END_DELIVERY_CERTIFICATION_CONTENT_LEN,
    MAX_PERSISTED_GOVERNED_END_TO_END_DELIVERY_CERTIFICATION_RECORDS,
    REQUIRED_CERTIFICATION_REVIEW_KINDS,
)

_DEFAULT_STORE = Path("data/execution_track_5_governed_end_to_end_delivery_certification/records.json")


def _utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def _store_path() -> Path:
    return Path(
        __import__("os").environ.get(
            "AETHOS_EXECUTION_TRACK_5_STORE",
            str(_DEFAULT_STORE),
        )
    )


def _load_raw() -> dict[str, Any]:
    path = _store_path()
    if not path.exists():
        return {"records": [], "delivery_run_registry": []}
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return {"records": [], "delivery_run_registry": []}
    if not isinstance(payload, dict):
        return {"records": [], "delivery_run_registry": []}
    if not isinstance(payload.get("records"), list):
        payload["records"] = []
    if not isinstance(payload.get("delivery_run_registry"), list):
        payload["delivery_run_registry"] = []
    return payload


def _save_raw(payload: dict[str, Any]) -> None:
    path = _store_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")


def list_governed_end_to_end_delivery_certification_records() -> list[dict[str, Any]]:
    return list(_load_raw().get("records") or [])


def list_delivery_run_registry_entries() -> list[dict[str, Any]]:
    return list(_load_raw().get("delivery_run_registry") or [])


def clear_governed_end_to_end_delivery_certification_records_for_tests() -> None:
    path = _store_path()
    if path.exists():
        path.unlink(missing_ok=True)


def has_certification_decision_approve(*, session_id: str | None = None) -> bool:
    for record in list_governed_end_to_end_delivery_certification_records():
        if session_id and str(record.get("session_id") or "") != session_id:
            continue
        if str(record.get("kind") or "") == "certification_decision_approve":
            return True
    return False


def has_certification_review_kind(*, kind: str, session_id: str | None = None) -> bool:
    for record in list_governed_end_to_end_delivery_certification_records():
        if session_id and str(record.get("session_id") or "") != session_id:
            continue
        if str(record.get("kind") or "") == kind:
            return True
    return False


def all_certification_reviews_recorded(*, session_id: str) -> bool:
    return all(
        has_certification_review_kind(kind=kind, session_id=session_id)
        for kind in REQUIRED_CERTIFICATION_REVIEW_KINDS
    )


def latest_record_by_kind(*, session_id: str, kind: str) -> dict[str, Any] | None:
    matches = [
        row
        for row in list_governed_end_to_end_delivery_certification_records()
        if str(row.get("kind") or "") == kind
        and str(row.get("session_id") or session_id) == session_id
    ]
    return matches[-1] if matches else None


def append_governed_end_to_end_delivery_certification_record(
    *,
    kind: str,
    content: str,
    session_id: str | None = None,
    metadata: dict[str, Any] | None = None,
) -> dict[str, Any]:
    normalized_kind = str(kind or "").strip()
    if normalized_kind not in GOVERNED_END_TO_END_DELIVERY_CERTIFICATION_RECORD_KINDS:
        raise ValueError(f"unsupported certification record kind: {kind!r}")

    normalized_content = str(content or "").strip()
    if not normalized_content:
        raise ValueError("content is required")
    if len(normalized_content) > MAX_GOVERNED_END_TO_END_DELIVERY_CERTIFICATION_CONTENT_LEN:
        raise ValueError("content exceeds maximum length")

    payload = _load_raw()
    records = list(payload.get("records") or [])
    record = {
        "schema_version": GOVERNED_END_TO_END_DELIVERY_CERTIFICATION_RECORD_SCHEMA_VERSION,
        "record_id": f"et5-{len(records) + 1:05d}",
        "kind": normalized_kind,
        "content": normalized_content,
        "session_id": (session_id or "default").strip()[:64] or "default",
        "metadata": dict(metadata or {}),
        "recorded_at": _utc_now(),
    }
    records.append(record)
    if len(records) > MAX_PERSISTED_GOVERNED_END_TO_END_DELIVERY_CERTIFICATION_RECORDS:
        records = records[-MAX_PERSISTED_GOVERNED_END_TO_END_DELIVERY_CERTIFICATION_RECORDS:]
    payload["records"] = records
    _save_raw(payload)
    return record


def register_delivery_run(*, entry: dict[str, Any]) -> dict[str, Any]:
    payload = _load_raw()
    registry = list(payload.get("delivery_run_registry") or [])
    normalized = dict(entry)
    normalized.setdefault("registered_at", _utc_now())
    existing_idx = None
    run_id = str(normalized.get("run_id") or "")
    for idx, row in enumerate(registry):
        if str(row.get("run_id") or "") == run_id and run_id:
            existing_idx = idx
            break
    if existing_idx is not None:
        registry[existing_idx] = normalized
    else:
        registry.append(normalized)
    payload["delivery_run_registry"] = registry
    _save_raw(payload)
    return normalized

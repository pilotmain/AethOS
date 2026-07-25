# SPDX-License-Identifier: Apache-2.0
"""FIX 316 — post-launch operations baseline store."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from aethos_core.mission_control.post_launch_operations_baseline.post_launch_operations_baseline_contract import (
    HUMAN_OPERATIONS_BASELINE_DECISION_KINDS,
    MAX_PERSISTED_POST_LAUNCH_OPERATIONS_BASELINE_RECORDS,
    MAX_POST_LAUNCH_OPERATIONS_BASELINE_CONTENT_LEN,
    POST_LAUNCH_OPERATIONS_BASELINE_RECORD_KINDS,
    POST_LAUNCH_OPERATIONS_BASELINE_RECORD_SCHEMA_VERSION,
)

_DEFAULT_STORE = Path("data/mission_control_post_launch_operations_baseline/records.json")


def _utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def _store_path() -> Path:
    return Path(
        __import__("os").environ.get(
            "AETHOS_POST_LAUNCH_OPERATIONS_BASELINE_STORE",
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


def list_post_launch_operations_baseline_records() -> list[dict[str, Any]]:
    return list(_load_raw().get("records") or [])


def clear_post_launch_operations_baseline_records_for_tests() -> None:
    path = _store_path()
    if path.exists():
        path.unlink(missing_ok=True)


def has_operations_baseline_review_decision_approve(*, session_id: str | None = None) -> bool:
    for record in list_post_launch_operations_baseline_records():
        if session_id and str(record.get("session_id") or "") != session_id:
            continue
        if str(record.get("kind") or "") == "operations_baseline_review_decision_approve":
            return True
    return False


def append_post_launch_operations_baseline_record(
    *,
    kind: str,
    content: str,
    session_id: str | None = None,
    domain: str | None = None,
) -> dict[str, Any]:
    normalized_kind = str(kind or "").strip()
    if normalized_kind not in POST_LAUNCH_OPERATIONS_BASELINE_RECORD_KINDS:
        raise ValueError(f"unsupported post launch operations baseline record kind: {kind!r}")

    normalized_content = str(content or "").strip()
    if not normalized_content:
        raise ValueError("content is required")
    if len(normalized_content) > MAX_POST_LAUNCH_OPERATIONS_BASELINE_CONTENT_LEN:
        raise ValueError("content exceeds maximum length")

    record: dict[str, Any] = {
        "schema_version": POST_LAUNCH_OPERATIONS_BASELINE_RECORD_SCHEMA_VERSION,
        "kind": normalized_kind,
        "content": normalized_content,
        "recorded_at": _utc_now(),
    }
    if session_id:
        record["session_id"] = str(session_id).strip()
    if domain:
        record["domain"] = str(domain).strip()
    if normalized_kind in HUMAN_OPERATIONS_BASELINE_DECISION_KINDS:
        record["operations_baseline_review_decision"] = normalized_kind.replace(
            "operations_baseline_review_decision_", ""
        )

    payload = _load_raw()
    records = list(payload.get("records") or [])
    records.append(record)
    payload["records"] = records[-MAX_PERSISTED_POST_LAUNCH_OPERATIONS_BASELINE_RECORDS:]
    _save_raw(payload)
    return record

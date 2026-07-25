# SPDX-License-Identifier: Apache-2.0
"""FIX 280 — autonomous application lifecycle management store."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from aethos_core.mission_control.autonomous_application_lifecycle_management.autonomous_application_lifecycle_management_contract import (
    AUTONOMOUS_APPLICATION_LIFECYCLE_MANAGEMENT_RECORD_KINDS,
    AUTONOMOUS_APPLICATION_LIFECYCLE_MANAGEMENT_RECORD_SCHEMA_VERSION,
    HUMAN_LIFECYCLE_DECISION_KINDS,
    LIFECYCLE_STAGES,
    MAX_AUTONOMOUS_APPLICATION_LIFECYCLE_MANAGEMENT_CONTENT_LEN,
    MAX_PERSISTED_AUTONOMOUS_APPLICATION_LIFECYCLE_MANAGEMENT_RECORDS,
)

_DEFAULT_STORE = Path("data/mission_control_autonomous_application_lifecycle_management/records.json")


def _utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def _store_path() -> Path:
    return Path(
        __import__("os").environ.get(
            "AETHOS_AUTONOMOUS_APPLICATION_LIFECYCLE_MANAGEMENT_STORE",
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


def list_autonomous_application_lifecycle_management_records() -> list[dict[str, Any]]:
    return list(_load_raw().get("records") or [])


def clear_autonomous_application_lifecycle_management_records_for_tests() -> None:
    path = _store_path()
    if path.exists():
        path.unlink(missing_ok=True)


def has_human_lifecycle_decision_approve(*, session_id: str | None = None) -> bool:
    for record in list_autonomous_application_lifecycle_management_records():
        if session_id and str(record.get("session_id") or "") != session_id:
            continue
        if str(record.get("kind") or "") == "human_lifecycle_decision_approve":
            return True
    return False


def append_autonomous_application_lifecycle_management_record(
    *,
    kind: str,
    content: str,
    session_id: str | None = None,
    lifecycle_stage: str | None = None,
    opportunity_id: str | None = None,
) -> dict[str, Any]:
    normalized_kind = str(kind or "").strip()
    if normalized_kind not in AUTONOMOUS_APPLICATION_LIFECYCLE_MANAGEMENT_RECORD_KINDS:
        raise ValueError(f"unsupported autonomous application lifecycle management record kind: {kind!r}")

    normalized_content = str(content or "").strip()
    if not normalized_content:
        raise ValueError("content is required")
    if len(normalized_content) > MAX_AUTONOMOUS_APPLICATION_LIFECYCLE_MANAGEMENT_CONTENT_LEN:
        raise ValueError("content exceeds maximum length")

    if lifecycle_stage is not None:
        stage = str(lifecycle_stage).strip()
        if stage and stage not in LIFECYCLE_STAGES:
            raise ValueError(f"unsupported lifecycle stage: {lifecycle_stage!r}")

    record: dict[str, Any] = {
        "schema_version": AUTONOMOUS_APPLICATION_LIFECYCLE_MANAGEMENT_RECORD_SCHEMA_VERSION,
        "kind": normalized_kind,
        "content": normalized_content,
        "recorded_at": _utc_now(),
    }
    if session_id:
        record["session_id"] = str(session_id).strip()
    if lifecycle_stage:
        record["lifecycle_stage"] = str(lifecycle_stage).strip()
    if opportunity_id:
        record["opportunity_id"] = str(opportunity_id).strip()
    if normalized_kind in HUMAN_LIFECYCLE_DECISION_KINDS:
        record["human_lifecycle_decision"] = normalized_kind.replace("human_lifecycle_decision_", "")

    payload = _load_raw()
    records = list(payload.get("records") or [])
    records.append(record)
    payload["records"] = records[-MAX_PERSISTED_AUTONOMOUS_APPLICATION_LIFECYCLE_MANAGEMENT_RECORDS:]
    _save_raw(payload)
    return record

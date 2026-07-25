# SPDX-License-Identifier: Apache-2.0
"""FIX 309 — SaaS launch readiness assessment store."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from aethos_core.mission_control.saas_launch_readiness_assessment.saas_launch_readiness_assessment_contract import (
    HUMAN_LAUNCH_READINESS_DECISION_KINDS,
    MAX_PERSISTED_SAAS_LAUNCH_READINESS_ASSESSMENT_RECORDS,
    MAX_SAAS_LAUNCH_READINESS_ASSESSMENT_CONTENT_LEN,
    SAAS_LAUNCH_READINESS_ASSESSMENT_RECORD_KINDS,
    SAAS_LAUNCH_READINESS_ASSESSMENT_RECORD_SCHEMA_VERSION,
)

_DEFAULT_STORE = Path("data/mission_control_saas_launch_readiness_assessment/records.json")


def _utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def _store_path() -> Path:
    return Path(
        __import__("os").environ.get(
            "AETHOS_SAAS_LAUNCH_READINESS_ASSESSMENT_STORE",
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


def list_saas_launch_readiness_assessment_records() -> list[dict[str, Any]]:
    return list(_load_raw().get("records") or [])


def clear_saas_launch_readiness_assessment_records_for_tests() -> None:
    path = _store_path()
    if path.exists():
        path.unlink(missing_ok=True)


def has_launch_readiness_decision_approve(*, session_id: str | None = None) -> bool:
    for record in list_saas_launch_readiness_assessment_records():
        if session_id and str(record.get("session_id") or "") != session_id:
            continue
        if str(record.get("kind") or "") == "launch_readiness_decision_approve":
            return True
    return False


def append_saas_launch_readiness_assessment_record(
    *,
    kind: str,
    content: str,
    session_id: str | None = None,
    domain: str | None = None,
) -> dict[str, Any]:
    normalized_kind = str(kind or "").strip()
    if normalized_kind not in SAAS_LAUNCH_READINESS_ASSESSMENT_RECORD_KINDS:
        raise ValueError(f"unsupported SaaS launch readiness assessment record kind: {kind!r}")

    normalized_content = str(content or "").strip()
    if not normalized_content:
        raise ValueError("content is required")
    if len(normalized_content) > MAX_SAAS_LAUNCH_READINESS_ASSESSMENT_CONTENT_LEN:
        raise ValueError("content exceeds maximum length")

    record: dict[str, Any] = {
        "schema_version": SAAS_LAUNCH_READINESS_ASSESSMENT_RECORD_SCHEMA_VERSION,
        "kind": normalized_kind,
        "content": normalized_content,
        "recorded_at": _utc_now(),
    }
    if session_id:
        record["session_id"] = str(session_id).strip()
    if domain:
        record["domain"] = str(domain).strip()
    if normalized_kind in HUMAN_LAUNCH_READINESS_DECISION_KINDS:
        record["launch_readiness_decision"] = normalized_kind.replace("launch_readiness_decision_", "")

    payload = _load_raw()
    records = list(payload.get("records") or [])
    records.append(record)
    payload["records"] = records[-MAX_PERSISTED_SAAS_LAUNCH_READINESS_ASSESSMENT_RECORDS:]
    _save_raw(payload)
    return record

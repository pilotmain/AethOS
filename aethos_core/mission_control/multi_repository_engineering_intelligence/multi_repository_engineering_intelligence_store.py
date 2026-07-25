# SPDX-License-Identifier: Apache-2.0
"""FIX 260 — multi-repository engineering intelligence store."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from aethos_core.mission_control.multi_repository_engineering_intelligence.multi_repository_engineering_intelligence_contract import (
    MAX_MULTI_REPOSITORY_ENGINEERING_INTELLIGENCE_CONTENT_LEN,
    MAX_PERSISTED_MULTI_REPOSITORY_ENGINEERING_INTELLIGENCE_RECORDS,
    MULTI_REPOSITORY_ENGINEERING_INTELLIGENCE_RECORD_KINDS,
    MULTI_REPOSITORY_ENGINEERING_INTELLIGENCE_RECORD_SCHEMA_VERSION,
    PORTFOLIO_REPOSITORIES,
)

_DEFAULT_STORE = Path("data/mission_control_multi_repository_engineering_intelligence/records.json")


def _utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def _store_path() -> Path:
    return Path(
        __import__("os").environ.get(
            "AETHOS_MULTI_REPOSITORY_ENGINEERING_INTELLIGENCE_STORE",
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


def list_multi_repository_engineering_intelligence_records() -> list[dict[str, Any]]:
    return list(_load_raw().get("records") or [])


def clear_multi_repository_engineering_intelligence_records_for_tests() -> None:
    path = _store_path()
    if path.exists():
        path.unlink(missing_ok=True)


def append_multi_repository_engineering_intelligence_record(
    *,
    kind: str,
    content: str,
    session_id: str | None = None,
    repository: str | None = None,
    source_repository: str | None = None,
    target_repository: str | None = None,
    relationship: str | None = None,
) -> dict[str, Any]:
    normalized_kind = str(kind or "").strip()
    if normalized_kind not in MULTI_REPOSITORY_ENGINEERING_INTELLIGENCE_RECORD_KINDS:
        raise ValueError(f"unsupported multi-repository engineering intelligence record kind: {kind!r}")

    normalized_content = str(content or "").strip()
    if not normalized_content:
        raise ValueError("content is required")
    if len(normalized_content) > MAX_MULTI_REPOSITORY_ENGINEERING_INTELLIGENCE_CONTENT_LEN:
        raise ValueError("content exceeds maximum length")

    if repository is not None:
        repo = str(repository).strip()
        if repo and repo not in PORTFOLIO_REPOSITORIES:
            raise ValueError(f"unsupported repository: {repository!r}")

    record = {
        "schema_version": MULTI_REPOSITORY_ENGINEERING_INTELLIGENCE_RECORD_SCHEMA_VERSION,
        "kind": normalized_kind,
        "content": normalized_content,
        "recorded_at": _utc_now(),
    }
    if session_id:
        record["session_id"] = str(session_id).strip()
    if repository:
        record["repository"] = str(repository).strip()
    if source_repository:
        record["source_repository"] = str(source_repository).strip()
    if target_repository:
        record["target_repository"] = str(target_repository).strip()
    if relationship:
        record["relationship"] = str(relationship).strip()

    payload = _load_raw()
    records = list(payload.get("records") or [])
    records.append(record)
    payload["records"] = records[-MAX_PERSISTED_MULTI_REPOSITORY_ENGINEERING_INTELLIGENCE_RECORDS:]
    _save_raw(payload)
    return record

# SPDX-License-Identifier: Apache-2.0
"""FIX 343 / WORKSTREAM_E1 — intelligence performance store."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from aethos_core.workstreams.intelligence_performance_evidence_scalability_program.intelligence_performance_evidence_scalability_program_contract import (
    INTELLIGENCE_PERFORMANCE_EVIDENCE_SCALABILITY_PROGRAM_RECORD_SCHEMA_VERSION,
    INTELLIGENCE_PERFORMANCE_RECORD_KINDS,
    MAX_INTELLIGENCE_PERFORMANCE_CONTENT_LEN,
    MAX_PERSISTED_INTELLIGENCE_PERFORMANCE_RECORDS,
)

_DEFAULT_STORE = Path("data/workstream_e1_intelligence_performance/records.json")


def _utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def _store_path() -> Path:
    return Path(
        __import__("os").environ.get(
            "AETHOS_WORKSTREAM_E1_STORE",
            str(_DEFAULT_STORE),
        )
    )


def _load_raw() -> dict[str, Any]:
    empty: dict[str, Any] = {
        "records": [],
        "compose_timing_registry": [],
        "compose_hotspot_registry": [],
        "performance_opportunity_registry": [],
    }
    path = _store_path()
    if not path.exists():
        return empty
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return empty
    if not isinstance(payload, dict):
        return empty
    for key in empty:
        if not isinstance(payload.get(key), list):
            payload[key] = []
    return payload


def _save_raw(payload: dict[str, Any]) -> None:
    path = _store_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")


def clear_intelligence_performance_records_for_tests() -> None:
    path = _store_path()
    if path.exists():
        path.unlink(missing_ok=True)


def list_intelligence_performance_records() -> list[dict[str, Any]]:
    return list(_load_raw().get("records") or [])


def list_compose_timing_registry_entries() -> list[dict[str, Any]]:
    return list(_load_raw().get("compose_timing_registry") or [])


def list_compose_hotspot_registry_entries() -> list[dict[str, Any]]:
    return list(_load_raw().get("compose_hotspot_registry") or [])


def list_performance_opportunity_registry_entries() -> list[dict[str, Any]]:
    return list(_load_raw().get("performance_opportunity_registry") or [])


def has_performance_review_approve(*, session_id: str | None = None) -> bool:
    for record in list_intelligence_performance_records():
        if session_id and str(record.get("session_id") or "") != session_id:
            continue
        if str(record.get("kind") or "") == "performance_review_approve":
            return True
    return False


def append_intelligence_performance_record(
    *,
    kind: str,
    content: str,
    session_id: str | None = None,
    metadata: dict[str, Any] | None = None,
) -> dict[str, Any]:
    normalized_kind = str(kind or "").strip()
    if normalized_kind not in INTELLIGENCE_PERFORMANCE_RECORD_KINDS:
        raise ValueError(f"unsupported intelligence performance record kind: {kind!r}")

    normalized_content = str(content or "").strip()
    if not normalized_content:
        raise ValueError("content is required")
    if len(normalized_content) > MAX_INTELLIGENCE_PERFORMANCE_CONTENT_LEN:
        raise ValueError("content exceeds maximum length")

    payload = _load_raw()
    records = list(payload.get("records") or [])
    record = {
        "schema_version": INTELLIGENCE_PERFORMANCE_EVIDENCE_SCALABILITY_PROGRAM_RECORD_SCHEMA_VERSION,
        "record_id": f"e1-{len(records) + 1:05d}",
        "kind": normalized_kind,
        "content": normalized_content,
        "session_id": (session_id or "default").strip()[:64] or "default",
        "metadata": dict(metadata or {}),
        "recorded_at": _utc_now(),
    }
    records.append(record)
    if len(records) > MAX_PERSISTED_INTELLIGENCE_PERFORMANCE_RECORDS:
        records = records[-MAX_PERSISTED_INTELLIGENCE_PERFORMANCE_RECORDS:]
    payload["records"] = records
    _save_raw(payload)
    return record


def register_compose_timing(*, entry: dict[str, Any]) -> dict[str, Any]:
    payload = _load_raw()
    registry = list(payload.get("compose_timing_registry") or [])
    normalized = dict(entry)
    normalized.setdefault("registered_at", _utc_now())
    timing_id = str(normalized.get("timing_id") or "")
    for idx, row in enumerate(registry):
        if str(row.get("timing_id") or "") == timing_id and timing_id:
            registry[idx] = normalized
            payload["compose_timing_registry"] = registry
            _save_raw(payload)
            return normalized
    registry.append(normalized)
    payload["compose_timing_registry"] = registry
    _save_raw(payload)
    return normalized


def register_compose_hotspot(*, entry: dict[str, Any]) -> dict[str, Any]:
    payload = _load_raw()
    registry = list(payload.get("compose_hotspot_registry") or [])
    normalized = dict(entry)
    normalized.setdefault("registered_at", _utc_now())
    hotspot_id = str(normalized.get("hotspot_id") or "")
    for idx, row in enumerate(registry):
        if str(row.get("hotspot_id") or "") == hotspot_id and hotspot_id:
            registry[idx] = normalized
            payload["compose_hotspot_registry"] = registry
            _save_raw(payload)
            return normalized
    registry.append(normalized)
    payload["compose_hotspot_registry"] = registry
    _save_raw(payload)
    return normalized


def register_performance_opportunity(*, entry: dict[str, Any]) -> dict[str, Any]:
    payload = _load_raw()
    registry = list(payload.get("performance_opportunity_registry") or [])
    normalized = dict(entry)
    normalized.setdefault("registered_at", _utc_now())
    opportunity_id = str(normalized.get("opportunity_id") or "")
    for idx, row in enumerate(registry):
        if str(row.get("opportunity_id") or "") == opportunity_id and opportunity_id:
            registry[idx] = normalized
            payload["performance_opportunity_registry"] = registry
            _save_raw(payload)
            return normalized
    registry.append(normalized)
    payload["performance_opportunity_registry"] = registry
    _save_raw(payload)
    return normalized

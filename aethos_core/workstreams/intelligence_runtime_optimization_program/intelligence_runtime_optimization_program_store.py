# SPDX-License-Identifier: Apache-2.0
"""FIX 344 / WORKSTREAM_E2 — intelligence runtime optimization store."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from aethos_core.workstreams.intelligence_runtime_optimization_program.intelligence_runtime_optimization_program_contract import (
    INTELLIGENCE_RUNTIME_OPTIMIZATION_PROGRAM_RECORD_SCHEMA_VERSION,
    INTELLIGENCE_RUNTIME_OPTIMIZATION_RECORD_KINDS,
    MAX_INTELLIGENCE_RUNTIME_OPTIMIZATION_CONTENT_LEN,
    MAX_PERSISTED_INTELLIGENCE_RUNTIME_OPTIMIZATION_RECORDS,
)

_DEFAULT_STORE = Path("data/workstream_e2_intelligence_runtime/records.json")


def _utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def _store_path() -> Path:
    return Path(
        __import__("os").environ.get(
            "AETHOS_WORKSTREAM_E2_STORE",
            str(_DEFAULT_STORE),
        )
    )


def _load_raw() -> dict[str, Any]:
    empty: dict[str, Any] = {
        "records": [],
        "runtime_dependency_registry": [],
        "runtime_hotspot_registry": [],
        "runtime_optimization_opportunity_registry": [],
        "runtime_metrics_registry": [],
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


def clear_intelligence_runtime_optimization_records_for_tests() -> None:
    path = _store_path()
    if path.exists():
        path.unlink(missing_ok=True)


def list_intelligence_runtime_optimization_records() -> list[dict[str, Any]]:
    return list(_load_raw().get("records") or [])


def list_runtime_dependency_registry_entries() -> list[dict[str, Any]]:
    return list(_load_raw().get("runtime_dependency_registry") or [])


def list_runtime_hotspot_registry_entries() -> list[dict[str, Any]]:
    return list(_load_raw().get("runtime_hotspot_registry") or [])


def list_runtime_optimization_opportunity_registry_entries() -> list[dict[str, Any]]:
    return list(_load_raw().get("runtime_optimization_opportunity_registry") or [])


def list_runtime_metrics_registry_entries() -> list[dict[str, Any]]:
    return list(_load_raw().get("runtime_metrics_registry") or [])


def has_runtime_optimization_review_approve(*, session_id: str | None = None) -> bool:
    for record in list_intelligence_runtime_optimization_records():
        if session_id and str(record.get("session_id") or "") != session_id:
            continue
        if str(record.get("kind") or "") == "runtime_optimization_review_approve":
            return True
    return False


def append_intelligence_runtime_optimization_record(
    *,
    kind: str,
    content: str,
    session_id: str | None = None,
    metadata: dict[str, Any] | None = None,
) -> dict[str, Any]:
    normalized_kind = str(kind or "").strip()
    if normalized_kind not in INTELLIGENCE_RUNTIME_OPTIMIZATION_RECORD_KINDS:
        raise ValueError(f"unsupported runtime optimization record kind: {kind!r}")

    normalized_content = str(content or "").strip()
    if not normalized_content:
        raise ValueError("content is required")
    if len(normalized_content) > MAX_INTELLIGENCE_RUNTIME_OPTIMIZATION_CONTENT_LEN:
        raise ValueError("content exceeds maximum length")

    payload = _load_raw()
    records = list(payload.get("records") or [])
    record = {
        "schema_version": INTELLIGENCE_RUNTIME_OPTIMIZATION_PROGRAM_RECORD_SCHEMA_VERSION,
        "record_id": f"e2-{len(records) + 1:05d}",
        "kind": normalized_kind,
        "content": normalized_content,
        "session_id": (session_id or "default").strip()[:64] or "default",
        "metadata": dict(metadata or {}),
        "recorded_at": _utc_now(),
    }
    records.append(record)
    if len(records) > MAX_PERSISTED_INTELLIGENCE_RUNTIME_OPTIMIZATION_RECORDS:
        records = records[-MAX_PERSISTED_INTELLIGENCE_RUNTIME_OPTIMIZATION_RECORDS:]
    payload["records"] = records
    _save_raw(payload)
    return record


def register_runtime_dependency(*, entry: dict[str, Any]) -> dict[str, Any]:
    payload = _load_raw()
    registry = list(payload.get("runtime_dependency_registry") or [])
    normalized = dict(entry)
    normalized.setdefault("registered_at", _utc_now())
    dep_id = str(normalized.get("dependency_id") or "")
    for idx, row in enumerate(registry):
        if str(row.get("dependency_id") or "") == dep_id and dep_id:
            registry[idx] = normalized
            payload["runtime_dependency_registry"] = registry
            _save_raw(payload)
            return normalized
    registry.append(normalized)
    payload["runtime_dependency_registry"] = registry
    _save_raw(payload)
    return normalized


def register_runtime_hotspot(*, entry: dict[str, Any]) -> dict[str, Any]:
    payload = _load_raw()
    registry = list(payload.get("runtime_hotspot_registry") or [])
    normalized = dict(entry)
    normalized.setdefault("registered_at", _utc_now())
    hotspot_id = str(normalized.get("hotspot_id") or "")
    for idx, row in enumerate(registry):
        if str(row.get("hotspot_id") or "") == hotspot_id and hotspot_id:
            registry[idx] = normalized
            payload["runtime_hotspot_registry"] = registry
            _save_raw(payload)
            return normalized
    registry.append(normalized)
    payload["runtime_hotspot_registry"] = registry
    _save_raw(payload)
    return normalized


def register_runtime_optimization_opportunity(*, entry: dict[str, Any]) -> dict[str, Any]:
    payload = _load_raw()
    registry = list(payload.get("runtime_optimization_opportunity_registry") or [])
    normalized = dict(entry)
    normalized.setdefault("registered_at", _utc_now())
    opportunity_id = str(normalized.get("opportunity_id") or "")
    for idx, row in enumerate(registry):
        if str(row.get("opportunity_id") or "") == opportunity_id and opportunity_id:
            registry[idx] = normalized
            payload["runtime_optimization_opportunity_registry"] = registry
            _save_raw(payload)
            return normalized
    registry.append(normalized)
    payload["runtime_optimization_opportunity_registry"] = registry
    _save_raw(payload)
    return normalized


def register_runtime_metrics(*, entry: dict[str, Any]) -> dict[str, Any]:
    payload = _load_raw()
    registry = list(payload.get("runtime_metrics_registry") or [])
    normalized = dict(entry)
    normalized.setdefault("registered_at", _utc_now())
    metrics_id = str(normalized.get("metrics_id") or "")
    for idx, row in enumerate(registry):
        if str(row.get("metrics_id") or "") == metrics_id and metrics_id:
            registry[idx] = normalized
            payload["runtime_metrics_registry"] = registry
            _save_raw(payload)
            return normalized
    registry.append(normalized)
    payload["runtime_metrics_registry"] = registry
    _save_raw(payload)
    return normalized

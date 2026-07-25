# SPDX-License-Identifier: Apache-2.0
"""FIX 345 / WORKSTREAM_E3 — intelligence scalability implementation store."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from aethos_core.workstreams.intelligence_scalability_implementation_program.intelligence_scalability_implementation_program_contract import (
    INTELLIGENCE_SCALABILITY_IMPLEMENTATION_PROGRAM_RECORD_SCHEMA_VERSION,
    INTELLIGENCE_SCALABILITY_RECORD_KINDS,
    MAX_INTELLIGENCE_SCALABILITY_CONTENT_LEN,
    MAX_PERSISTED_INTELLIGENCE_SCALABILITY_RECORDS,
)

_DEFAULT_STORE = Path("data/workstream_e3_intelligence_scalability/records.json")


def _utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def _store_path() -> Path:
    return Path(
        __import__("os").environ.get(
            "AETHOS_WORKSTREAM_E3_STORE",
            str(_DEFAULT_STORE),
        )
    )


def _load_raw() -> dict[str, Any]:
    empty: dict[str, Any] = {
        "records": [],
        "scalability_opportunity_registry": [],
        "runtime_benchmark_registry": [],
        "implementation_registry": [],
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


def clear_intelligence_scalability_implementation_records_for_tests() -> None:
    path = _store_path()
    if path.exists():
        path.unlink(missing_ok=True)


def list_intelligence_scalability_records() -> list[dict[str, Any]]:
    return list(_load_raw().get("records") or [])


def list_scalability_opportunity_registry_entries() -> list[dict[str, Any]]:
    return list(_load_raw().get("scalability_opportunity_registry") or [])


def list_runtime_benchmark_registry_entries() -> list[dict[str, Any]]:
    return list(_load_raw().get("runtime_benchmark_registry") or [])


def list_implementation_registry_entries() -> list[dict[str, Any]]:
    return list(_load_raw().get("implementation_registry") or [])


def has_scalability_review_approve(*, session_id: str | None = None) -> bool:
    for record in list_intelligence_scalability_records():
        if session_id and str(record.get("session_id") or "") != session_id:
            continue
        if str(record.get("kind") or "") == "scalability_review_approve":
            return True
    return False


def append_intelligence_scalability_record(
    *,
    kind: str,
    content: str,
    session_id: str | None = None,
    metadata: dict[str, Any] | None = None,
) -> dict[str, Any]:
    normalized_kind = str(kind or "").strip()
    if normalized_kind not in INTELLIGENCE_SCALABILITY_RECORD_KINDS:
        raise ValueError(f"unsupported scalability record kind: {kind!r}")

    normalized_content = str(content or "").strip()
    if not normalized_content:
        raise ValueError("content is required")
    if len(normalized_content) > MAX_INTELLIGENCE_SCALABILITY_CONTENT_LEN:
        raise ValueError("content exceeds maximum length")

    payload = _load_raw()
    records = list(payload.get("records") or [])
    record = {
        "schema_version": INTELLIGENCE_SCALABILITY_IMPLEMENTATION_PROGRAM_RECORD_SCHEMA_VERSION,
        "record_id": f"e3-{len(records) + 1:05d}",
        "kind": normalized_kind,
        "content": normalized_content,
        "session_id": (session_id or "default").strip()[:64] or "default",
        "metadata": dict(metadata or {}),
        "recorded_at": _utc_now(),
    }
    records.append(record)
    if len(records) > MAX_PERSISTED_INTELLIGENCE_SCALABILITY_RECORDS:
        records = records[-MAX_PERSISTED_INTELLIGENCE_SCALABILITY_RECORDS:]
    payload["records"] = records
    _save_raw(payload)
    return record


def register_scalability_opportunity(*, entry: dict[str, Any]) -> dict[str, Any]:
    payload = _load_raw()
    registry = list(payload.get("scalability_opportunity_registry") or [])
    normalized = dict(entry)
    normalized.setdefault("registered_at", _utc_now())
    opportunity_id = str(normalized.get("opportunity_id") or "")
    for idx, row in enumerate(registry):
        if str(row.get("opportunity_id") or "") == opportunity_id and opportunity_id:
            registry[idx] = normalized
            payload["scalability_opportunity_registry"] = registry
            _save_raw(payload)
            return normalized
    registry.append(normalized)
    payload["scalability_opportunity_registry"] = registry
    _save_raw(payload)
    return normalized


def register_runtime_benchmark(*, entry: dict[str, Any]) -> dict[str, Any]:
    payload = _load_raw()
    registry = list(payload.get("runtime_benchmark_registry") or [])
    normalized = dict(entry)
    normalized.setdefault("registered_at", _utc_now())
    benchmark_id = str(normalized.get("benchmark_id") or "")
    for idx, row in enumerate(registry):
        if str(row.get("benchmark_id") or "") == benchmark_id and benchmark_id:
            registry[idx] = normalized
            payload["runtime_benchmark_registry"] = registry
            _save_raw(payload)
            return normalized
    registry.append(normalized)
    payload["runtime_benchmark_registry"] = registry
    _save_raw(payload)
    return normalized


def register_implementation_entry(*, entry: dict[str, Any]) -> dict[str, Any]:
    payload = _load_raw()
    registry = list(payload.get("implementation_registry") or [])
    normalized = dict(entry)
    normalized.setdefault("registered_at", _utc_now())
    implementation_id = str(normalized.get("implementation_id") or "")
    for idx, row in enumerate(registry):
        if str(row.get("implementation_id") or "") == implementation_id and implementation_id:
            registry[idx] = normalized
            payload["implementation_registry"] = registry
            _save_raw(payload)
            return normalized
    registry.append(normalized)
    payload["implementation_registry"] = registry
    _save_raw(payload)
    return normalized

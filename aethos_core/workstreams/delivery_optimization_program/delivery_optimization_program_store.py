# SPDX-License-Identifier: Apache-2.0
"""FIX 340 / WORKSTREAM_C2 — delivery optimization store."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from aethos_core.workstreams.delivery_optimization_program.delivery_optimization_program_contract import (
    DELIVERY_OPTIMIZATION_PROGRAM_RECORD_SCHEMA_VERSION,
    DELIVERY_OPTIMIZATION_RECORD_KINDS,
    MAX_DELIVERY_OPTIMIZATION_CONTENT_LEN,
    MAX_PERSISTED_DELIVERY_OPTIMIZATION_RECORDS,
)

_DEFAULT_STORE = Path("data/workstream_c2_delivery_optimization/records.json")


def _utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def _store_path() -> Path:
    return Path(
        __import__("os").environ.get(
            "AETHOS_WORKSTREAM_C2_STORE",
            str(_DEFAULT_STORE),
        )
    )


def _load_raw() -> dict[str, Any]:
    path = _store_path()
    if not path.exists():
        return {
            "records": [],
            "delivery_outcome_registry": [],
            "delivery_improvement_opportunity_registry": [],
        }
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return {
            "records": [],
            "delivery_outcome_registry": [],
            "delivery_improvement_opportunity_registry": [],
        }
    if not isinstance(payload, dict):
        return {
            "records": [],
            "delivery_outcome_registry": [],
            "delivery_improvement_opportunity_registry": [],
        }
    for key in ("records", "delivery_outcome_registry", "delivery_improvement_opportunity_registry"):
        if not isinstance(payload.get(key), list):
            payload[key] = []
    return payload


def _save_raw(payload: dict[str, Any]) -> None:
    path = _store_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")


def clear_delivery_optimization_records_for_tests() -> None:
    path = _store_path()
    if path.exists():
        path.unlink(missing_ok=True)


def list_delivery_optimization_records() -> list[dict[str, Any]]:
    return list(_load_raw().get("records") or [])


def list_delivery_outcome_registry_entries() -> list[dict[str, Any]]:
    return list(_load_raw().get("delivery_outcome_registry") or [])


def list_delivery_improvement_opportunity_registry_entries() -> list[dict[str, Any]]:
    return list(_load_raw().get("delivery_improvement_opportunity_registry") or [])


def has_delivery_optimization_review_approve(*, session_id: str | None = None) -> bool:
    for record in list_delivery_optimization_records():
        if session_id and str(record.get("session_id") or "") != session_id:
            continue
        if str(record.get("kind") or "") == "delivery_optimization_review_approve":
            return True
    return False


def append_delivery_optimization_record(
    *,
    kind: str,
    content: str,
    session_id: str | None = None,
    metadata: dict[str, Any] | None = None,
) -> dict[str, Any]:
    normalized_kind = str(kind or "").strip()
    if normalized_kind not in DELIVERY_OPTIMIZATION_RECORD_KINDS:
        raise ValueError(f"unsupported delivery optimization record kind: {kind!r}")

    normalized_content = str(content or "").strip()
    if not normalized_content:
        raise ValueError("content is required")
    if len(normalized_content) > MAX_DELIVERY_OPTIMIZATION_CONTENT_LEN:
        raise ValueError("content exceeds maximum length")

    payload = _load_raw()
    records = list(payload.get("records") or [])
    record = {
        "schema_version": DELIVERY_OPTIMIZATION_PROGRAM_RECORD_SCHEMA_VERSION,
        "record_id": f"c2-{len(records) + 1:05d}",
        "kind": normalized_kind,
        "content": normalized_content,
        "session_id": (session_id or "default").strip()[:64] or "default",
        "metadata": dict(metadata or {}),
        "recorded_at": _utc_now(),
    }
    records.append(record)
    if len(records) > MAX_PERSISTED_DELIVERY_OPTIMIZATION_RECORDS:
        records = records[-MAX_PERSISTED_DELIVERY_OPTIMIZATION_RECORDS:]
    payload["records"] = records
    _save_raw(payload)
    return record


def register_delivery_outcome(*, entry: dict[str, Any]) -> dict[str, Any]:
    payload = _load_raw()
    registry = list(payload.get("delivery_outcome_registry") or [])
    normalized = dict(entry)
    normalized.setdefault("registered_at", _utc_now())
    outcome_id = str(normalized.get("outcome_id") or "")
    for idx, row in enumerate(registry):
        if str(row.get("outcome_id") or "") == outcome_id and outcome_id:
            registry[idx] = normalized
            payload["delivery_outcome_registry"] = registry
            _save_raw(payload)
            return normalized
    registry.append(normalized)
    payload["delivery_outcome_registry"] = registry
    _save_raw(payload)
    return normalized


def register_improvement_opportunity(*, entry: dict[str, Any]) -> dict[str, Any]:
    payload = _load_raw()
    registry = list(payload.get("delivery_improvement_opportunity_registry") or [])
    normalized = dict(entry)
    normalized.setdefault("registered_at", _utc_now())
    opportunity_id = str(normalized.get("opportunity_id") or "")
    for idx, row in enumerate(registry):
        if str(row.get("opportunity_id") or "") == opportunity_id and opportunity_id:
            registry[idx] = normalized
            payload["delivery_improvement_opportunity_registry"] = registry
            _save_raw(payload)
            return normalized
    registry.append(normalized)
    payload["delivery_improvement_opportunity_registry"] = registry
    _save_raw(payload)
    return normalized

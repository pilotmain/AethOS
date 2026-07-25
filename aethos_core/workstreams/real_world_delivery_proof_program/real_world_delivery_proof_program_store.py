# SPDX-License-Identifier: Apache-2.0
"""FIX 339 / WORKSTREAM_C1 — real world delivery proof store."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from aethos_core.workstreams.real_world_delivery_proof_program.real_world_delivery_proof_program_contract import (
    MAX_PERSISTED_REAL_WORLD_DELIVERY_PROOF_RECORDS,
    MAX_REAL_WORLD_DELIVERY_PROOF_CONTENT_LEN,
    REAL_WORLD_DELIVERY_PROOF_PROGRAM_RECORD_SCHEMA_VERSION,
    REAL_WORLD_DELIVERY_PROOF_RECORD_KINDS,
)

_DEFAULT_STORE = Path("data/workstream_c1_real_world_delivery_proof/records.json")


def _utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def _store_path() -> Path:
    return Path(
        __import__("os").environ.get(
            "AETHOS_WORKSTREAM_C1_STORE",
            str(_DEFAULT_STORE),
        )
    )


def _load_raw() -> dict[str, Any]:
    path = _store_path()
    if not path.exists():
        return {
            "records": [],
            "delivery_candidate_registry": [],
            "delivery_execution_registry": [],
            "delivery_verification_registry": [],
            "delivery_incident_registry": [],
        }
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return {
            "records": [],
            "delivery_candidate_registry": [],
            "delivery_execution_registry": [],
            "delivery_verification_registry": [],
            "delivery_incident_registry": [],
        }
    if not isinstance(payload, dict):
        return {
            "records": [],
            "delivery_candidate_registry": [],
            "delivery_execution_registry": [],
            "delivery_verification_registry": [],
            "delivery_incident_registry": [],
        }
    for key in (
        "records",
        "delivery_candidate_registry",
        "delivery_execution_registry",
        "delivery_verification_registry",
        "delivery_incident_registry",
    ):
        if not isinstance(payload.get(key), list):
            payload[key] = []
    return payload


def _save_raw(payload: dict[str, Any]) -> None:
    path = _store_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")


def clear_real_world_delivery_proof_records_for_tests() -> None:
    path = _store_path()
    if path.exists():
        path.unlink(missing_ok=True)


def list_real_world_delivery_proof_records() -> list[dict[str, Any]]:
    return list(_load_raw().get("records") or [])


def list_delivery_candidate_registry_entries() -> list[dict[str, Any]]:
    return list(_load_raw().get("delivery_candidate_registry") or [])


def list_delivery_execution_registry_entries() -> list[dict[str, Any]]:
    return list(_load_raw().get("delivery_execution_registry") or [])


def list_delivery_verification_registry_entries() -> list[dict[str, Any]]:
    return list(_load_raw().get("delivery_verification_registry") or [])


def list_delivery_incident_registry_entries() -> list[dict[str, Any]]:
    return list(_load_raw().get("delivery_incident_registry") or [])


def has_delivery_proof_review_approve(*, session_id: str | None = None) -> bool:
    for record in list_real_world_delivery_proof_records():
        if session_id and str(record.get("session_id") or "") != session_id:
            continue
        if str(record.get("kind") or "") == "delivery_proof_review_approve":
            return True
    return False


def latest_record_by_kind(*, session_id: str, kind: str) -> dict[str, Any] | None:
    matches = [
        row
        for row in list_real_world_delivery_proof_records()
        if str(row.get("kind") or "") == kind
        and str(row.get("session_id") or session_id) == session_id
    ]
    return matches[-1] if matches else None


def append_real_world_delivery_proof_record(
    *,
    kind: str,
    content: str,
    session_id: str | None = None,
    metadata: dict[str, Any] | None = None,
) -> dict[str, Any]:
    normalized_kind = str(kind or "").strip()
    if normalized_kind not in REAL_WORLD_DELIVERY_PROOF_RECORD_KINDS:
        raise ValueError(f"unsupported delivery proof record kind: {kind!r}")

    normalized_content = str(content or "").strip()
    if not normalized_content:
        raise ValueError("content is required")
    if len(normalized_content) > MAX_REAL_WORLD_DELIVERY_PROOF_CONTENT_LEN:
        raise ValueError("content exceeds maximum length")

    payload = _load_raw()
    records = list(payload.get("records") or [])
    record = {
        "schema_version": REAL_WORLD_DELIVERY_PROOF_PROGRAM_RECORD_SCHEMA_VERSION,
        "record_id": f"c1-{len(records) + 1:05d}",
        "kind": normalized_kind,
        "content": normalized_content,
        "session_id": (session_id or "default").strip()[:64] or "default",
        "metadata": dict(metadata or {}),
        "recorded_at": _utc_now(),
    }
    records.append(record)
    if len(records) > MAX_PERSISTED_REAL_WORLD_DELIVERY_PROOF_RECORDS:
        records = records[-MAX_PERSISTED_REAL_WORLD_DELIVERY_PROOF_RECORDS:]
    payload["records"] = records
    _save_raw(payload)
    return record


def register_delivery_candidate(*, entry: dict[str, Any]) -> dict[str, Any]:
    payload = _load_raw()
    registry = list(payload.get("delivery_candidate_registry") or [])
    normalized = dict(entry)
    normalized.setdefault("registered_at", _utc_now())
    candidate_id = str(normalized.get("candidate_id") or "")
    for idx, row in enumerate(registry):
        if str(row.get("candidate_id") or "") == candidate_id and candidate_id:
            registry[idx] = normalized
            payload["delivery_candidate_registry"] = registry
            _save_raw(payload)
            return normalized
    registry.append(normalized)
    payload["delivery_candidate_registry"] = registry
    _save_raw(payload)
    return normalized


def register_delivery_execution(*, entry: dict[str, Any]) -> dict[str, Any]:
    payload = _load_raw()
    registry = list(payload.get("delivery_execution_registry") or [])
    normalized = dict(entry)
    normalized.setdefault("registered_at", _utc_now())
    execution_id = str(normalized.get("execution_id") or "")
    for idx, row in enumerate(registry):
        if str(row.get("execution_id") or "") == execution_id and execution_id:
            registry[idx] = normalized
            payload["delivery_execution_registry"] = registry
            _save_raw(payload)
            return normalized
    registry.append(normalized)
    payload["delivery_execution_registry"] = registry
    _save_raw(payload)
    return normalized


def register_delivery_verification(*, entry: dict[str, Any]) -> dict[str, Any]:
    payload = _load_raw()
    registry = list(payload.get("delivery_verification_registry") or [])
    normalized = dict(entry)
    normalized.setdefault("registered_at", _utc_now())
    verification_id = str(normalized.get("verification_id") or "")
    for idx, row in enumerate(registry):
        if str(row.get("verification_id") or "") == verification_id and verification_id:
            registry[idx] = normalized
            payload["delivery_verification_registry"] = registry
            _save_raw(payload)
            return normalized
    registry.append(normalized)
    payload["delivery_verification_registry"] = registry
    _save_raw(payload)
    return normalized


def register_delivery_incident(*, entry: dict[str, Any]) -> dict[str, Any]:
    payload = _load_raw()
    registry = list(payload.get("delivery_incident_registry") or [])
    normalized = dict(entry)
    normalized.setdefault("registered_at", _utc_now())
    incident_id = str(normalized.get("incident_id") or "")
    for idx, row in enumerate(registry):
        if str(row.get("incident_id") or "") == incident_id and incident_id:
            registry[idx] = normalized
            payload["delivery_incident_registry"] = registry
            _save_raw(payload)
            return normalized
    registry.append(normalized)
    payload["delivery_incident_registry"] = registry
    _save_raw(payload)
    return normalized

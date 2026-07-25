# SPDX-License-Identifier: Apache-2.0
"""FIX 341 / WORKSTREAM_D1 — Phase 2 provider execution expansion store."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from aethos_core.workstreams.phase2_provider_execution_expansion_program.phase2_provider_execution_expansion_program_contract import (
    MAX_PERSISTED_PHASE2_PROVIDER_EXPANSION_RECORDS,
    MAX_PHASE2_PROVIDER_EXPANSION_CONTENT_LEN,
    PHASE2_PROVIDER_EXECUTION_EXPANSION_PROGRAM_RECORD_SCHEMA_VERSION,
    PHASE2_PROVIDER_EXECUTION_EXPANSION_RECORD_KINDS,
    WAVE_1_PROVIDER_ORDER,
)

_DEFAULT_STORE = Path("data/workstream_d1_phase2_provider_execution_expansion/records.json")


def _utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def _store_path() -> Path:
    return Path(
        __import__("os").environ.get(
            "AETHOS_WORKSTREAM_D1_STORE",
            str(_DEFAULT_STORE),
        )
    )


def _load_raw() -> dict[str, Any]:
    path = _store_path()
    empty: dict[str, Any] = {
        "records": [],
        "provider_expansion_registry": [],
        "phase2_execution_registry": [],
        "verification_registry": [],
    }
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


def clear_phase2_provider_execution_expansion_records_for_tests() -> None:
    path = _store_path()
    if path.exists():
        path.unlink(missing_ok=True)


def list_phase2_provider_execution_expansion_records() -> list[dict[str, Any]]:
    return list(_load_raw().get("records") or [])


def list_provider_expansion_registry_entries() -> list[dict[str, Any]]:
    return list(_load_raw().get("provider_expansion_registry") or [])


def list_phase2_execution_registry_entries() -> list[dict[str, Any]]:
    return list(_load_raw().get("phase2_execution_registry") or [])


def list_phase2_verification_registry_entries() -> list[dict[str, Any]]:
    return list(_load_raw().get("verification_registry") or [])


def _normalize_provider(value: str | None) -> str | None:
    raw = str(value or "").strip().lower()
    aliases = {
        "aws": "AWS",
        "amazon": "AWS",
        "kubernetes": "Kubernetes",
        "k8s": "Kubernetes",
        "kube": "Kubernetes",
        "azure": "Azure",
        "az": "Azure",
        "gcp": "GCP",
        "google": "GCP",
    }
    if raw in aliases:
        return aliases[raw]
    if value in WAVE_1_PROVIDER_ORDER:
        return value
    return None


def has_phase2_provider_expansion_approve(*, session_id: str | None = None) -> bool:
    for record in list_phase2_provider_execution_expansion_records():
        if session_id and str(record.get("session_id") or "") != session_id:
            continue
        if str(record.get("kind") or "") == "phase2_provider_expansion_review_approve":
            return True
    return False


def has_provider_readiness_review(*, session_id: str, provider: str) -> bool:
    normalized = _normalize_provider(provider)
    for record in list_phase2_provider_execution_expansion_records():
        if str(record.get("session_id") or "") != session_id:
            continue
        if str(record.get("kind") or "") != "phase2_provider_readiness_review_note":
            continue
        meta = record.get("metadata") or {}
        if _normalize_provider(meta.get("provider")) == normalized:
            return True
    return False


def has_provider_execution_review(*, session_id: str, provider: str) -> bool:
    normalized = _normalize_provider(provider)
    for record in list_phase2_provider_execution_expansion_records():
        if str(record.get("session_id") or "") != session_id:
            continue
        if str(record.get("kind") or "") != "phase2_provider_execution_review_note":
            continue
        meta = record.get("metadata") or {}
        if _normalize_provider(meta.get("provider")) == normalized:
            return True
    return False


def has_provider_execution_readiness(*, session_id: str, provider: str) -> bool:
    return (
        has_phase2_provider_expansion_approve(session_id=session_id)
        and has_provider_readiness_review(session_id=session_id, provider=provider)
        and has_provider_execution_review(session_id=session_id, provider=provider)
    )


def latest_record_by_kind(*, session_id: str, kind: str) -> dict[str, Any] | None:
    matches = [
        row
        for row in list_phase2_provider_execution_expansion_records()
        if str(row.get("kind") or "") == kind
        and str(row.get("session_id") or session_id) == session_id
    ]
    return matches[-1] if matches else None


def append_phase2_provider_execution_expansion_record(
    *,
    kind: str,
    content: str,
    session_id: str | None = None,
    metadata: dict[str, Any] | None = None,
) -> dict[str, Any]:
    normalized_kind = str(kind or "").strip()
    if normalized_kind not in PHASE2_PROVIDER_EXECUTION_EXPANSION_RECORD_KINDS:
        raise ValueError(f"unsupported phase2 expansion record kind: {kind!r}")

    normalized_content = str(content or "").strip()
    if not normalized_content:
        raise ValueError("content is required")
    if len(normalized_content) > MAX_PHASE2_PROVIDER_EXPANSION_CONTENT_LEN:
        raise ValueError("content exceeds maximum length")

    payload = _load_raw()
    records = list(payload.get("records") or [])
    record = {
        "schema_version": PHASE2_PROVIDER_EXECUTION_EXPANSION_PROGRAM_RECORD_SCHEMA_VERSION,
        "record_id": f"d1-{len(records) + 1:05d}",
        "kind": normalized_kind,
        "content": normalized_content,
        "session_id": (session_id or "default").strip()[:64] or "default",
        "metadata": dict(metadata or {}),
        "recorded_at": _utc_now(),
    }
    records.append(record)
    if len(records) > MAX_PERSISTED_PHASE2_PROVIDER_EXPANSION_RECORDS:
        records = records[-MAX_PERSISTED_PHASE2_PROVIDER_EXPANSION_RECORDS:]
    payload["records"] = records
    _save_raw(payload)
    return record


def register_provider_expansion(*, entry: dict[str, Any]) -> dict[str, Any]:
    payload = _load_raw()
    registry = list(payload.get("provider_expansion_registry") or [])
    normalized = dict(entry)
    normalized.setdefault("registered_at", _utc_now())
    provider = str(normalized.get("provider") or "")
    for idx, row in enumerate(registry):
        if str(row.get("provider") or "") == provider and provider:
            registry[idx] = normalized
            payload["provider_expansion_registry"] = registry
            _save_raw(payload)
            return normalized
    registry.append(normalized)
    payload["provider_expansion_registry"] = registry
    _save_raw(payload)
    return normalized


def register_phase2_execution(*, entry: dict[str, Any]) -> dict[str, Any]:
    payload = _load_raw()
    registry = list(payload.get("phase2_execution_registry") or [])
    normalized = dict(entry)
    normalized.setdefault("registered_at", _utc_now())
    execution_id = str(normalized.get("execution_id") or "")
    for idx, row in enumerate(registry):
        if str(row.get("execution_id") or "") == execution_id and execution_id:
            registry[idx] = normalized
            payload["phase2_execution_registry"] = registry
            _save_raw(payload)
            return normalized
    registry.append(normalized)
    payload["phase2_execution_registry"] = registry
    _save_raw(payload)
    return normalized


def register_phase2_verification(*, entry: dict[str, Any]) -> dict[str, Any]:
    payload = _load_raw()
    registry = list(payload.get("verification_registry") or [])
    normalized = dict(entry)
    normalized.setdefault("registered_at", _utc_now())
    verification_id = str(normalized.get("verification_id") or "")
    for idx, row in enumerate(registry):
        if str(row.get("verification_id") or "") == verification_id and verification_id:
            registry[idx] = normalized
            payload["verification_registry"] = registry
            _save_raw(payload)
            return normalized
    registry.append(normalized)
    payload["verification_registry"] = registry
    _save_raw(payload)
    return normalized

# SPDX-License-Identifier: Apache-2.0
"""FIX 342 / WORKSTREAM_D2 — multi-cloud operational proof store."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from aethos_core.workstreams.multi_cloud_operational_proof_program.multi_cloud_operational_proof_program_contract import (
    ALL_PROOF_PROVIDERS,
    MAX_MULTI_CLOUD_OPERATIONAL_PROOF_CONTENT_LEN,
    MAX_PERSISTED_MULTI_CLOUD_OPERATIONAL_PROOF_RECORDS,
    MULTI_CLOUD_OPERATIONAL_PROOF_PROGRAM_RECORD_SCHEMA_VERSION,
    MULTI_CLOUD_OPERATIONAL_PROOF_RECORD_KINDS,
)

_DEFAULT_STORE = Path("data/workstream_d2_multi_cloud_operational_proof/records.json")


def _utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def _store_path() -> Path:
    return Path(
        __import__("os").environ.get(
            "AETHOS_WORKSTREAM_D2_STORE",
            str(_DEFAULT_STORE),
        )
    )


def _load_raw() -> dict[str, Any]:
    empty: dict[str, Any] = {
        "records": [],
        "deployment_candidate_registry": [],
        "provider_execution_registry": [],
        "provider_verification_registry": [],
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


def clear_multi_cloud_operational_proof_records_for_tests() -> None:
    path = _store_path()
    if path.exists():
        path.unlink(missing_ok=True)


def list_multi_cloud_operational_proof_records() -> list[dict[str, Any]]:
    return list(_load_raw().get("records") or [])


def list_deployment_candidate_registry_entries() -> list[dict[str, Any]]:
    return list(_load_raw().get("deployment_candidate_registry") or [])


def list_provider_execution_registry_entries() -> list[dict[str, Any]]:
    return list(_load_raw().get("provider_execution_registry") or [])


def list_provider_verification_registry_entries() -> list[dict[str, Any]]:
    return list(_load_raw().get("provider_verification_registry") or [])


def _normalize_provider(value: str | None) -> str | None:
    raw = str(value or "").strip().lower()
    aliases = {
        "railway": "Railway",
        "rail": "Railway",
        "vercel": "Vercel",
        "vc": "Vercel",
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
    if value in ALL_PROOF_PROVIDERS:
        return value
    return None


def has_provider_proof_review_approve(*, session_id: str | None = None) -> bool:
    for record in list_multi_cloud_operational_proof_records():
        if session_id and str(record.get("session_id") or "") != session_id:
            continue
        if str(record.get("kind") or "") == "provider_proof_review_approve":
            return True
    return False


def append_multi_cloud_operational_proof_record(
    *,
    kind: str,
    content: str,
    session_id: str | None = None,
    metadata: dict[str, Any] | None = None,
) -> dict[str, Any]:
    normalized_kind = str(kind or "").strip()
    if normalized_kind not in MULTI_CLOUD_OPERATIONAL_PROOF_RECORD_KINDS:
        raise ValueError(f"unsupported multi-cloud proof record kind: {kind!r}")

    normalized_content = str(content or "").strip()
    if not normalized_content:
        raise ValueError("content is required")
    if len(normalized_content) > MAX_MULTI_CLOUD_OPERATIONAL_PROOF_CONTENT_LEN:
        raise ValueError("content exceeds maximum length")

    payload = _load_raw()
    records = list(payload.get("records") or [])
    record = {
        "schema_version": MULTI_CLOUD_OPERATIONAL_PROOF_PROGRAM_RECORD_SCHEMA_VERSION,
        "record_id": f"d2-{len(records) + 1:05d}",
        "kind": normalized_kind,
        "content": normalized_content,
        "session_id": (session_id or "default").strip()[:64] or "default",
        "metadata": dict(metadata or {}),
        "recorded_at": _utc_now(),
    }
    records.append(record)
    if len(records) > MAX_PERSISTED_MULTI_CLOUD_OPERATIONAL_PROOF_RECORDS:
        records = records[-MAX_PERSISTED_MULTI_CLOUD_OPERATIONAL_PROOF_RECORDS:]
    payload["records"] = records
    _save_raw(payload)
    return record


def register_deployment_candidate(*, entry: dict[str, Any]) -> dict[str, Any]:
    payload = _load_raw()
    registry = list(payload.get("deployment_candidate_registry") or [])
    normalized = dict(entry)
    normalized.setdefault("registered_at", _utc_now())
    candidate_id = str(normalized.get("candidate_id") or "")
    for idx, row in enumerate(registry):
        if str(row.get("candidate_id") or "") == candidate_id and candidate_id:
            registry[idx] = normalized
            payload["deployment_candidate_registry"] = registry
            _save_raw(payload)
            return normalized
    registry.append(normalized)
    payload["deployment_candidate_registry"] = registry
    _save_raw(payload)
    return normalized


def register_provider_execution(*, entry: dict[str, Any]) -> dict[str, Any]:
    payload = _load_raw()
    registry = list(payload.get("provider_execution_registry") or [])
    normalized = dict(entry)
    normalized.setdefault("registered_at", _utc_now())
    execution_id = str(normalized.get("execution_id") or "")
    for idx, row in enumerate(registry):
        if str(row.get("execution_id") or "") == execution_id and execution_id:
            registry[idx] = normalized
            payload["provider_execution_registry"] = registry
            _save_raw(payload)
            return normalized
    registry.append(normalized)
    payload["provider_execution_registry"] = registry
    _save_raw(payload)
    return normalized


def register_provider_verification(*, entry: dict[str, Any]) -> dict[str, Any]:
    payload = _load_raw()
    registry = list(payload.get("provider_verification_registry") or [])
    normalized = dict(entry)
    normalized.setdefault("registered_at", _utc_now())
    verification_id = str(normalized.get("verification_id") or "")
    for idx, row in enumerate(registry):
        if str(row.get("verification_id") or "") == verification_id and verification_id:
            registry[idx] = normalized
            payload["provider_verification_registry"] = registry
            _save_raw(payload)
            return normalized
    registry.append(normalized)
    payload["provider_verification_registry"] = registry
    _save_raw(payload)
    return normalized

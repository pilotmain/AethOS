# SPDX-License-Identifier: Apache-2.0
"""FIX 346 / WORKSTREAM_E4 — compose runtime guardrails store."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from aethos_core.workstreams.compose_runtime_guardrails_program.compose_runtime_guardrails_program_contract import (
    COMPOSE_RUNTIME_GUARDRAILS_PROGRAM_RECORD_SCHEMA_VERSION,
    COMPOSE_RUNTIME_GUARDRAILS_RECORD_KINDS,
    MAX_COMPOSE_RUNTIME_GUARDRAILS_CONTENT_LEN,
    MAX_PERSISTED_COMPOSE_RUNTIME_GUARDRAILS_RECORDS,
)

_DEFAULT_STORE = Path("data/workstream_e4_compose_runtime_guardrails/records.json")


def _utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def _store_path() -> Path:
    return Path(
        __import__("os").environ.get(
            "AETHOS_WORKSTREAM_E4_STORE",
            str(_DEFAULT_STORE),
        )
    )


def _load_raw() -> dict[str, Any]:
    empty: dict[str, Any] = {"records": [], "benchmark_command_registry": []}
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


def clear_compose_runtime_guardrails_records_for_tests() -> None:
    path = _store_path()
    if path.exists():
        path.unlink(missing_ok=True)


def list_compose_runtime_guardrails_records() -> list[dict[str, Any]]:
    return list(_load_raw().get("records") or [])


def list_benchmark_command_registry_entries() -> list[dict[str, Any]]:
    return list(_load_raw().get("benchmark_command_registry") or [])


def has_runtime_guardrail_review_approve(*, session_id: str | None = None) -> bool:
    for record in list_compose_runtime_guardrails_records():
        if session_id and str(record.get("session_id") or "") != session_id:
            continue
        if str(record.get("kind") or "") == "runtime_guardrail_review_approve":
            return True
    return False


def append_compose_runtime_guardrails_record(
    *,
    kind: str,
    content: str,
    session_id: str | None = None,
    metadata: dict[str, Any] | None = None,
) -> dict[str, Any]:
    normalized_kind = str(kind or "").strip()
    if normalized_kind not in COMPOSE_RUNTIME_GUARDRAILS_RECORD_KINDS:
        raise ValueError(f"unsupported guardrail record kind: {kind!r}")

    normalized_content = str(content or "").strip()
    if not normalized_content:
        raise ValueError("content is required")
    if len(normalized_content) > MAX_COMPOSE_RUNTIME_GUARDRAILS_CONTENT_LEN:
        raise ValueError("content exceeds maximum length")

    payload = _load_raw()
    records = list(payload.get("records") or [])
    record = {
        "schema_version": COMPOSE_RUNTIME_GUARDRAILS_PROGRAM_RECORD_SCHEMA_VERSION,
        "record_id": f"e4-{len(records) + 1:05d}",
        "kind": normalized_kind,
        "content": normalized_content,
        "session_id": (session_id or "default").strip()[:64] or "default",
        "metadata": dict(metadata or {}),
        "recorded_at": _utc_now(),
    }
    records.append(record)
    if len(records) > MAX_PERSISTED_COMPOSE_RUNTIME_GUARDRAILS_RECORDS:
        records = records[-MAX_PERSISTED_COMPOSE_RUNTIME_GUARDRAILS_RECORDS:]
    payload["records"] = records
    _save_raw(payload)
    return record


def register_benchmark_command(*, entry: dict[str, Any]) -> dict[str, Any]:
    payload = _load_raw()
    registry = list(payload.get("benchmark_command_registry") or [])
    normalized = dict(entry)
    normalized.setdefault("registered_at", _utc_now())
    command_id = str(normalized.get("command_id") or "")
    for idx, row in enumerate(registry):
        if str(row.get("command_id") or "") == command_id and command_id:
            registry[idx] = normalized
            payload["benchmark_command_registry"] = registry
            _save_raw(payload)
            return normalized
    registry.append(normalized)
    payload["benchmark_command_registry"] = registry
    _save_raw(payload)
    return normalized

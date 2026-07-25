# SPDX-License-Identifier: Apache-2.0
"""FIX 356 / WORKSTREAM_G3 — revenue density & business viability store."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from aethos_core.workstreams.revenue_density_business_viability_program.revenue_density_business_viability_program_contract import (
    MAX_PERSISTED_REVENUE_DENSITY_RECORDS,
    MAX_REVENUE_DENSITY_CONTENT_LEN,
    REVENUE_DENSITY_BUSINESS_VIABILITY_PROGRAM_RECORD_SCHEMA_VERSION,
    REVENUE_DENSITY_RECORD_KINDS,
)

_DEFAULT_STORE = Path("data/workstream_g3_revenue_density_business_viability/records.json")


def _utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def _store_path() -> Path:
    return Path(
        __import__("os").environ.get(
            "AETHOS_WORKSTREAM_G3_STORE",
            str(_DEFAULT_STORE),
        )
    )


def _load_raw() -> dict[str, Any]:
    empty: dict[str, Any] = {"records": [], "revenue_cohort_registry": []}
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


def clear_revenue_density_records_for_tests() -> None:
    path = _store_path()
    if path.exists():
        path.unlink(missing_ok=True)


def list_revenue_density_records() -> list[dict[str, Any]]:
    return list(_load_raw().get("records") or [])


def list_revenue_cohort_registry_entries() -> list[dict[str, Any]]:
    return list(_load_raw().get("revenue_cohort_registry") or [])


def has_revenue_density_review_approve(*, program_session_id: str | None = None) -> bool:
    for record in list_revenue_density_records():
        if program_session_id and str(record.get("session_id") or "") != program_session_id:
            continue
        if str(record.get("kind") or "") == "revenue_density_review_approve":
            return True
    return False


def register_revenue_cohort_customer(*, entry: dict[str, Any]) -> dict[str, Any]:
    payload = _load_raw()
    registry = list(payload.get("revenue_cohort_registry") or [])
    normalized = dict(entry)
    normalized.setdefault("registered_at", _utc_now())
    customer_id = str(normalized.get("customer_id") or "")
    for idx, row in enumerate(registry):
        if str(row.get("customer_id") or "") == customer_id and customer_id:
            registry[idx] = normalized
            payload["revenue_cohort_registry"] = registry
            _save_raw(payload)
            return normalized
    registry.append(normalized)
    payload["revenue_cohort_registry"] = registry
    _save_raw(payload)
    return normalized


def append_revenue_density_record(
    *,
    kind: str,
    content: str,
    session_id: str | None = None,
    metadata: dict[str, Any] | None = None,
) -> dict[str, Any]:
    normalized_kind = str(kind or "").strip()
    if normalized_kind not in REVENUE_DENSITY_RECORD_KINDS:
        raise ValueError(f"unsupported revenue density record kind: {kind!r}")

    normalized_content = str(content or "").strip()
    if not normalized_content:
        raise ValueError("content is required")
    if len(normalized_content) > MAX_REVENUE_DENSITY_CONTENT_LEN:
        raise ValueError("content exceeds maximum length")

    payload = _load_raw()
    records = list(payload.get("records") or [])
    record = {
        "schema_version": REVENUE_DENSITY_BUSINESS_VIABILITY_PROGRAM_RECORD_SCHEMA_VERSION,
        "record_id": f"g3-{len(records) + 1:05d}",
        "kind": normalized_kind,
        "content": normalized_content,
        "session_id": (session_id or "default").strip()[:64] or "default",
        "metadata": dict(metadata or {}),
        "recorded_at": _utc_now(),
    }
    records.append(record)
    if len(records) > MAX_PERSISTED_REVENUE_DENSITY_RECORDS:
        records = records[-MAX_PERSISTED_REVENUE_DENSITY_RECORDS:]
    payload["records"] = records
    _save_raw(payload)
    return record

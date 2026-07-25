# SPDX-License-Identifier: Apache-2.0
"""FIX 300 — multi-tenant platform foundation store."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from aethos_core.mission_control.multi_tenant_platform_foundation.multi_tenant_platform_foundation_contract import (
    HUMAN_TENANT_DECISION_KINDS,
    MAX_MULTI_TENANT_PLATFORM_FOUNDATION_CONTENT_LEN,
    MAX_PERSISTED_MULTI_TENANT_PLATFORM_FOUNDATION_RECORDS,
    MULTI_TENANT_PLATFORM_FOUNDATION_RECORD_KINDS,
    MULTI_TENANT_PLATFORM_FOUNDATION_RECORD_SCHEMA_VERSION,
    TENANT_DOMAINS,
)

_DEFAULT_STORE = Path("data/mission_control_multi_tenant_platform_foundation/records.json")


def _utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def _store_path() -> Path:
    return Path(
        __import__("os").environ.get(
            "AETHOS_MULTI_TENANT_PLATFORM_FOUNDATION_STORE",
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


def list_multi_tenant_platform_foundation_records() -> list[dict[str, Any]]:
    return list(_load_raw().get("records") or [])


def clear_multi_tenant_platform_foundation_records_for_tests() -> None:
    path = _store_path()
    if path.exists():
        path.unlink(missing_ok=True)


def has_human_tenant_decision_approve(*, session_id: str | None = None) -> bool:
    for record in list_multi_tenant_platform_foundation_records():
        if session_id and str(record.get("session_id") or "") != session_id:
            continue
        if str(record.get("kind") or "") == "human_tenant_decision_approve":
            return True
    return False


def append_multi_tenant_platform_foundation_record(
    *,
    kind: str,
    content: str,
    session_id: str | None = None,
    tenant_domain: str | None = None,
    organization_id: str | None = None,
    workspace_id: str | None = None,
    project_id: str | None = None,
) -> dict[str, Any]:
    normalized_kind = str(kind or "").strip()
    if normalized_kind not in MULTI_TENANT_PLATFORM_FOUNDATION_RECORD_KINDS:
        raise ValueError(f"unsupported multi-tenant platform foundation record kind: {kind!r}")

    normalized_content = str(content or "").strip()
    if not normalized_content:
        raise ValueError("content is required")
    if len(normalized_content) > MAX_MULTI_TENANT_PLATFORM_FOUNDATION_CONTENT_LEN:
        raise ValueError("content exceeds maximum length")

    if tenant_domain is not None:
        domain = str(tenant_domain).strip()
        if domain and domain not in TENANT_DOMAINS:
            raise ValueError(f"unsupported tenant domain: {tenant_domain!r}")

    record: dict[str, Any] = {
        "schema_version": MULTI_TENANT_PLATFORM_FOUNDATION_RECORD_SCHEMA_VERSION,
        "kind": normalized_kind,
        "content": normalized_content,
        "recorded_at": _utc_now(),
    }
    if session_id:
        record["session_id"] = str(session_id).strip()
    if tenant_domain:
        record["tenant_domain"] = str(tenant_domain).strip()
    if organization_id:
        record["organization_id"] = str(organization_id).strip()
    if workspace_id:
        record["workspace_id"] = str(workspace_id).strip()
    if project_id:
        record["project_id"] = str(project_id).strip()
    if normalized_kind in HUMAN_TENANT_DECISION_KINDS:
        record["human_tenant_decision"] = normalized_kind.replace("human_tenant_decision_", "")

    payload = _load_raw()
    records = list(payload.get("records") or [])
    records.append(record)
    payload["records"] = records[-MAX_PERSISTED_MULTI_TENANT_PLATFORM_FOUNDATION_RECORDS:]
    _save_raw(payload)
    return record

# SPDX-License-Identifier: Apache-2.0
"""FIX 301 — tenant onboarding and activation store."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from aethos_core.mission_control.tenant_onboarding_activation.tenant_onboarding_activation_contract import (
    HUMAN_ONBOARDING_DECISION_KINDS,
    MAX_PERSISTED_TENANT_ONBOARDING_ACTIVATION_RECORDS,
    MAX_TENANT_ONBOARDING_ACTIVATION_CONTENT_LEN,
    TENANT_ONBOARDING_ACTIVATION_RECORD_KINDS,
    TENANT_ONBOARDING_ACTIVATION_RECORD_SCHEMA_VERSION,
)

_DEFAULT_STORE = Path("data/mission_control_tenant_onboarding_activation/records.json")


def _utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def _store_path() -> Path:
    return Path(
        __import__("os").environ.get(
            "AETHOS_TENANT_ONBOARDING_ACTIVATION_STORE",
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


def list_tenant_onboarding_activation_records() -> list[dict[str, Any]]:
    return list(_load_raw().get("records") or [])


def clear_tenant_onboarding_activation_records_for_tests() -> None:
    path = _store_path()
    if path.exists():
        path.unlink(missing_ok=True)


def has_onboarding_decision_approve(*, session_id: str | None = None) -> bool:
    for record in list_tenant_onboarding_activation_records():
        if session_id and str(record.get("session_id") or "") != session_id:
            continue
        if str(record.get("kind") or "") == "onboarding_decision_approve":
            return True
    return False


def has_onboarding_record_kind(*, kind: str, session_id: str | None = None) -> bool:
    for record in list_tenant_onboarding_activation_records():
        if session_id and str(record.get("session_id") or "") != session_id:
            continue
        if str(record.get("kind") or "") == kind:
            return True
    return False


def append_tenant_onboarding_activation_record(
    *,
    kind: str,
    content: str,
    session_id: str | None = None,
    onboarding_step: str | None = None,
    organization_id: str | None = None,
    workspace_id: str | None = None,
    project_id: str | None = None,
) -> dict[str, Any]:
    normalized_kind = str(kind or "").strip()
    if normalized_kind not in TENANT_ONBOARDING_ACTIVATION_RECORD_KINDS:
        raise ValueError(f"unsupported tenant onboarding activation record kind: {kind!r}")

    normalized_content = str(content or "").strip()
    if not normalized_content:
        raise ValueError("content is required")
    if len(normalized_content) > MAX_TENANT_ONBOARDING_ACTIVATION_CONTENT_LEN:
        raise ValueError("content exceeds maximum length")

    record: dict[str, Any] = {
        "schema_version": TENANT_ONBOARDING_ACTIVATION_RECORD_SCHEMA_VERSION,
        "kind": normalized_kind,
        "content": normalized_content,
        "recorded_at": _utc_now(),
    }
    if session_id:
        record["session_id"] = str(session_id).strip()
    if onboarding_step:
        record["onboarding_step"] = str(onboarding_step).strip()
    if organization_id:
        record["organization_id"] = str(organization_id).strip()
    if workspace_id:
        record["workspace_id"] = str(workspace_id).strip()
    if project_id:
        record["project_id"] = str(project_id).strip()
    if normalized_kind in HUMAN_ONBOARDING_DECISION_KINDS:
        record["onboarding_decision"] = normalized_kind.replace("onboarding_decision_", "")

    payload = _load_raw()
    records = list(payload.get("records") or [])
    records.append(record)
    payload["records"] = records[-MAX_PERSISTED_TENANT_ONBOARDING_ACTIVATION_RECORDS:]
    _save_raw(payload)
    return record

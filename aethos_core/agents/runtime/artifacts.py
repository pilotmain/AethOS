# SPDX-License-Identifier: Apache-2.0
"""Agent artifact storage — auditable delegation evidence (tenant-scoped)."""

from __future__ import annotations

import json
import os
import stat
from pathlib import Path
from time import time
from typing import Any
from uuid import uuid4

from aethos_core.agents.runtime.agent_limits import ARTIFACT_TYPES
from aethos_core.agents.runtime.paths import agent_artifacts_root

_NS = "agent_artifact"


def new_artifact_id() -> str:
    return f"aart-{uuid4().hex[:12]}"


def _index_path() -> Path:
    return agent_artifacts_root() / "index.json"


def _atomic_write(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(".tmp")
    tmp.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    os.chmod(tmp, stat.S_IRUSR | stat.S_IWUSR)
    tmp.replace(path)


def store_agent_artifact(
    *,
    artifact_type: str,
    agent_id: str | None,
    plan_id: str | None,
    payload: dict[str, Any],
    summary: str = "",
    tenant_id: str | None = None,
) -> dict[str, Any]:
    if artifact_type not in ARTIFACT_TYPES:
        raise ValueError(f"Unknown agent artifact type: {artifact_type}")
    from aethos_core.tenancy.tenant_data_store import resolve_data_tenant, set_record

    tid = resolve_data_tenant(tenant_id)
    artifact_id = new_artifact_id()
    record: dict[str, Any] = {
        "artifact_id": artifact_id,
        "artifact_type": artifact_type,
        "agent_id": agent_id,
        "plan_id": plan_id,
        "tenant_id": tid,
        "created_at": time(),
        "summary": summary[:500],
        "payload": payload,
        "read_only": True,
    }
    set_record(_NS, artifact_id, record, tenant_id=tid)
    return record


def list_agent_artifacts(*, limit: int = 40, tenant_id: str | None = None) -> list[dict[str, Any]]:
    from aethos_core.tenancy.tenant_data_store import list_records, resolve_data_tenant

    tid = resolve_data_tenant(tenant_id)
    rows = list_records(_NS, tenant_id=tid, limit=limit)
    if rows:
        return [
            {
                "artifact_id": row.get("artifact_id"),
                "artifact_type": row.get("artifact_type"),
                "agent_id": row.get("agent_id"),
                "plan_id": row.get("plan_id"),
                "created_at": row.get("created_at"),
                "summary": row.get("summary"),
            }
            for row in rows
        ]
    # Legacy file index (default tenant migration).
    if tid != "default":
        return []
    legacy = _load_legacy_index()[:limit]
    return legacy


def get_agent_artifact(artifact_id: str, *, tenant_id: str | None = None) -> dict[str, Any] | None:
    from aethos_core.tenancy.tenant_data_store import get_record_by_namespace_key, resolve_data_tenant

    tid = resolve_data_tenant(tenant_id)
    record = get_record_by_namespace_key(_NS, artifact_id, tenant_id=tid)
    if record:
        return record
    if tid != "default":
        return None
    path = agent_artifacts_root() / "records" / f"{artifact_id}.json"
    if not path.is_file():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None


def _load_legacy_index() -> list[dict[str, Any]]:
    path = _index_path()
    if not path.is_file():
        return []
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
        rows = raw.get("artifacts") if isinstance(raw, dict) else raw
        return list(rows) if isinstance(rows, list) else []
    except (OSError, json.JSONDecodeError):
        return []

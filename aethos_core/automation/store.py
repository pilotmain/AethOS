# SPDX-License-Identifier: Apache-2.0
"""Tenant-scoped automation store — scheduled tasks and webhook triggers."""

from __future__ import annotations

import hashlib
import secrets
from time import time
from typing import Any
from uuid import uuid4

from aethos_core.tenancy.tenant_context import DEFAULT_TENANT
from aethos_core.tenancy.tenant_data_store import (
    delete_record,
    get_record,
    list_records,
    set_record,
)

NS_SCHEDULED = "automation_scheduled"
NS_WEBHOOK = "automation_webhooks"
NS_WEBHOOK_INDEX = "automation_webhook_index"
NS_RUNS = "automation_runs"


def _now() -> float:
    return time()


def _hash_secret(secret: str) -> str:
    return hashlib.sha256(secret.encode("utf-8")).hexdigest()


def _new_id(prefix: str) -> str:
    return f"{prefix}-{uuid4().hex[:12]}"


def build_delivery_session_id(*, channel: str, target: str = "default") -> str:
    ch = (channel or "web").strip().lower() or "web"
    tgt = (target or "default").strip() or "default"
    if ch == "web":
        return f"web-{tgt}"[:64]
    return f"{ch}-{tgt}"[:64]


# ── Scheduled tasks ───────────────────────────────────────────────────────────


def create_scheduled_task(
    *,
    name: str,
    prompt: str,
    schedule_kind: str = "interval",
    cron_expression: str | None = None,
    interval_sec: int = 3600,
    action_kind: str = "chat",
    job_type: str | None = None,
    delivery_channel: str = "web",
    delivery_target: str = "default",
    enabled: bool = True,
    tenant_id: str | None = None,
) -> dict[str, Any]:
    task_id = _new_id("sched")
    row = {
        "task_id": task_id,
        "name": (name or "Scheduled task").strip()[:120],
        "prompt": (prompt or "").strip()[:4000],
        "schedule_kind": schedule_kind if schedule_kind in {"cron", "interval"} else "interval",
        "cron_expression": (cron_expression or "").strip()[:80] or None,
        "interval_sec": max(60, int(interval_sec or 3600)),
        "action_kind": action_kind if action_kind in {"chat", "governed_job"} else "chat",
        "job_type": (job_type or "").strip()[:80] or None,
        "delivery_channel": (delivery_channel or "web").strip().lower()[:24],
        "delivery_target": (delivery_target or "default").strip()[:120],
        "session_id": build_delivery_session_id(
            channel=delivery_channel, target=delivery_target
        ),
        "enabled": bool(enabled),
        "created_at": _now(),
        "updated_at": _now(),
        "last_run_at": None,
        "last_status": None,
    }
    set_record(NS_SCHEDULED, task_id, row, tenant_id=tenant_id)
    return row


def list_scheduled_tasks(*, tenant_id: str | None = None, limit: int = 50) -> list[dict[str, Any]]:
    return list_records(NS_SCHEDULED, tenant_id=tenant_id, limit=limit)


def get_scheduled_task(task_id: str, *, tenant_id: str | None = None) -> dict[str, Any] | None:
    from aethos_core.tenancy.tenant_data_store import get_record_by_namespace_key

    return get_record_by_namespace_key(NS_SCHEDULED, task_id, tenant_id=tenant_id)


def update_scheduled_task(task_id: str, patch: dict[str, Any], *, tenant_id: str | None = None) -> dict[str, Any] | None:
    row = get_scheduled_task(task_id, tenant_id=tenant_id)
    if not row:
        return None
    for key, value in patch.items():
        if key in {"task_id", "created_at"}:
            continue
        if key == "enabled":
            row["enabled"] = bool(value)
        elif key == "interval_sec":
            row["interval_sec"] = max(60, int(value or 60))
        elif key in row:
            row[key] = value
    row["updated_at"] = _now()
    if "delivery_channel" in patch or "delivery_target" in patch:
        row["session_id"] = build_delivery_session_id(
            channel=str(row.get("delivery_channel") or "web"),
            target=str(row.get("delivery_target") or "default"),
        )
    set_record(NS_SCHEDULED, task_id, row, tenant_id=tenant_id)
    return row


def delete_scheduled_task(task_id: str, *, tenant_id: str | None = None) -> bool:
    return delete_record(NS_SCHEDULED, task_id, tenant_id=tenant_id)


def list_all_enabled_scheduled_tasks() -> list[dict[str, Any]]:
    """Cross-tenant scan for the scheduler loop (tasks carry tenant via store scope)."""
    from aethos_core.tenancy.tenant_data_store import _connect, _lock

    out: list[dict[str, Any]] = []
    try:
        with _lock:
            rows = _connect().execute(
                "SELECT tenant_id, record_key, payload FROM tenant_records "
                "WHERE namespace = ? ORDER BY updated_at DESC",
                (NS_SCHEDULED,),
            ).fetchall()
        import json

        for tenant_id, record_key, payload in rows:
            try:
                row = json.loads(str(payload))
            except (json.JSONDecodeError, TypeError):
                continue
            if not isinstance(row, dict) or not row.get("enabled"):
                continue
            row["_tenant_id"] = str(tenant_id)
            row.setdefault("task_id", record_key)
            out.append(row)
    except Exception:
        return []
    return out


# ── Webhook triggers ──────────────────────────────────────────────────────────


def _index_webhook(trigger_id: str, tenant_id: str) -> None:
    set_record(
        NS_WEBHOOK_INDEX,
        trigger_id,
        {"tenant_id": tenant_id, "trigger_id": trigger_id},
        tenant_id=DEFAULT_TENANT,
    )


def _unindex_webhook(trigger_id: str) -> None:
    delete_record(NS_WEBHOOK_INDEX, trigger_id, tenant_id=DEFAULT_TENANT)


def resolve_webhook_tenant(trigger_id: str) -> str | None:
    data = get_record(NS_WEBHOOK_INDEX, trigger_id, tenant_id=DEFAULT_TENANT, default=None)
    if isinstance(data, dict):
        tid = str(data.get("tenant_id") or "").strip()
        return tid or None
    return None


def create_webhook_trigger(
    *,
    name: str,
    prompt: str,
    action_kind: str = "chat",
    job_type: str | None = None,
    delivery_channel: str = "web",
    delivery_target: str = "default",
    allow_mutation: bool = False,
    enabled: bool = True,
    tenant_id: str | None = None,
) -> dict[str, Any]:
    from aethos_core.tenancy.tenant_data_store import resolve_data_tenant

    tid = resolve_data_tenant(tenant_id)
    trigger_id = _new_id("hook")
    secret = secrets.token_urlsafe(24)
    row = {
        "trigger_id": trigger_id,
        "name": (name or "Webhook trigger").strip()[:120],
        "prompt": (prompt or "").strip()[:4000],
        "action_kind": action_kind if action_kind in {"chat", "governed_job"} else "chat",
        "job_type": (job_type or "").strip()[:80] or None,
        "delivery_channel": (delivery_channel or "web").strip().lower()[:24],
        "delivery_target": (delivery_target or "default").strip()[:120],
        "session_id": build_delivery_session_id(
            channel=delivery_channel, target=delivery_target
        ),
        "allow_mutation": bool(allow_mutation),
        "enabled": bool(enabled),
        "secret_hash": _hash_secret(secret),
        "created_at": _now(),
        "updated_at": _now(),
        "last_fired_at": None,
        "fire_count": 0,
        "webhook_url_path": f"/api/v1/automation/webhooks/{trigger_id}",
    }
    set_record(NS_WEBHOOK, trigger_id, row, tenant_id=tid)
    _index_webhook(trigger_id, tid)
    return {**row, "secret": secret}


def list_webhook_triggers(*, tenant_id: str | None = None, limit: int = 50) -> list[dict[str, Any]]:
    rows = list_records(NS_WEBHOOK, tenant_id=tenant_id, limit=limit)
    return [{k: v for k, v in row.items() if k != "secret_hash"} for row in rows]


def get_webhook_trigger(trigger_id: str, *, tenant_id: str | None = None) -> dict[str, Any] | None:
    from aethos_core.tenancy.tenant_data_store import get_record_by_namespace_key

    row = get_record_by_namespace_key(NS_WEBHOOK, trigger_id, tenant_id=tenant_id)
    if not row:
        return None
    return {k: v for k, v in row.items() if k != "secret_hash"}


def get_webhook_trigger_with_secret_hash(
    trigger_id: str, *, tenant_id: str | None = None
) -> dict[str, Any] | None:
    from aethos_core.tenancy.tenant_data_store import get_record_by_namespace_key

    return get_record_by_namespace_key(NS_WEBHOOK, trigger_id, tenant_id=tenant_id)


def update_webhook_trigger(
    trigger_id: str, patch: dict[str, Any], *, tenant_id: str | None = None
) -> dict[str, Any] | None:
    row = get_webhook_trigger_with_secret_hash(trigger_id, tenant_id=tenant_id)
    if not row:
        return None
    secret_hash = row.get("secret_hash")
    for key, value in patch.items():
        if key in {"trigger_id", "created_at", "secret_hash"}:
            continue
        if key == "enabled":
            row["enabled"] = bool(value)
        elif key == "allow_mutation":
            row["allow_mutation"] = bool(value)
        elif key in row:
            row[key] = value
    row["updated_at"] = _now()
    if secret_hash:
        row["secret_hash"] = secret_hash
    if "delivery_channel" in patch or "delivery_target" in patch:
        row["session_id"] = build_delivery_session_id(
            channel=str(row.get("delivery_channel") or "web"),
            target=str(row.get("delivery_target") or "default"),
        )
    set_record(NS_WEBHOOK, trigger_id, row, tenant_id=tenant_id)
    return {k: v for k, v in row.items() if k != "secret_hash"}


def delete_webhook_trigger(trigger_id: str, *, tenant_id: str | None = None) -> bool:
    ok = delete_record(NS_WEBHOOK, trigger_id, tenant_id=tenant_id)
    if ok:
        _unindex_webhook(trigger_id)
    return ok


def verify_webhook_secret(trigger: dict[str, Any], secret: str) -> bool:
    expected = str(trigger.get("secret_hash") or "")
    if not expected or not secret:
        return False
    return secrets.compare_digest(expected, _hash_secret(secret))


def record_automation_run(
    *,
    kind: str,
    ref_id: str,
    status: str,
    detail: dict[str, Any] | None = None,
    tenant_id: str | None = None,
) -> None:
    run_id = _new_id("run")
    set_record(
        NS_RUNS,
        run_id,
        {
            "run_id": run_id,
            "kind": kind,
            "ref_id": ref_id,
            "status": status,
            "detail": dict(detail or {}),
            "at": _now(),
        },
        tenant_id=tenant_id,
    )


def clear_automation_for_tests() -> None:
    from aethos_core.tenancy.tenant_data_store import clear_namespace, reset_for_tests

    reset_for_tests()

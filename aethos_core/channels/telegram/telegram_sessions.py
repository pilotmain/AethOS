# SPDX-License-Identifier: Apache-2.0
"""Enrich Telegram session list with job/approval context."""

from __future__ import annotations

from typing import Any

from aethos_core.channels.dispatch import APPROVABLE_PREFLIGHT
from aethos_core.channels.telegram.telegram_activity import list_sessions
from aethos_core.channels.telegram.telegram_identity import is_telegram_session
from aethos_core.runtime.job_types import uses_operation_preflight


def _session_state(*, pending_job_id: str | None, last_operation: str | None) -> str:
    if pending_job_id:
        return "awaiting_approval"
    if last_operation:
        return "active"
    return "idle"


def list_telegram_sessions(*, limit: int = 50) -> list[dict[str, Any]]:
    from aethos_core.runtime.jobs import job_store

    pending_by_session: dict[str, str] = {}
    for job in job_store.list_all():
        if not is_telegram_session(job.session_id):
            continue
        if job.status != "completed":
            continue
        if not uses_operation_preflight(job.job_type):
            continue
        pf = job.params.get("operation_preflight") if isinstance(job.params.get("operation_preflight"), dict) else {}
        status = str(job.params.get("preflight_status") or pf.get("preflight_status") or "")
        if status in APPROVABLE_PREFLIGHT:
            pending_by_session[job.session_id] = job.id

    rows: list[dict[str, Any]] = []
    for entry in list_sessions(limit=limit):
        sid = str(entry.get("session_id") or "")
        pending = pending_by_session.get(sid)
        enriched = dict(entry)
        enriched["pending_approval_job_id"] = pending
        enriched["session_state"] = _session_state(
            pending_job_id=pending,
            last_operation=str(entry.get("last_operation") or "") or None,
        )
        rows.append(enriched)
    return rows

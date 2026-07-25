# SPDX-License-Identifier: Apache-2.0
"""Job notifications — Telegram / MC completion notices."""

from __future__ import annotations

import json
from pathlib import Path
from time import time
from typing import Any
from uuid import uuid4


def _root() -> Path:
    root = Path(__file__).resolve().parents[2] / "data" / "conversation" / "job_notifications"
    root.mkdir(parents=True, exist_ok=True)
    return root


def enqueue_job_notification(
    *,
    session_id: str,
    channel: str = "telegram",
    message: str,
    job_id: str | None = None,
    job_type: str | None = None,
) -> dict[str, Any]:
    from aethos_core.job_truth.notification_policy import should_enqueue_notification

    pending = list_pending_notifications(session_id=session_id)
    if not should_enqueue_notification(job_type=job_type, message=message, pending_count=len(pending)):
        return {"notification_id": None, "suppressed": True, "session_id": session_id}
    row = {
        "notification_id": f"jn-{uuid4().hex[:10]}",
        "session_id": session_id,
        "channel": channel,
        "message": message[:1200],
        "job_id": job_id,
        "job_type": job_type,
        "delivered": False,
        "created_at": time(),
    }
    path = _root() / f"pending_{session_id.replace('/', '_')[:80]}.json"
    pending: list[dict[str, Any]] = []
    if path.is_file():
        try:
            pending = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            pending = []
    pending.insert(0, row)
    path.write_text(json.dumps(pending[:20], indent=2), encoding="utf-8")
    return row


def list_pending_notifications(*, session_id: str) -> list[dict[str, Any]]:
    path = _root() / f"pending_{session_id.replace('/', '_')[:80]}.json"
    if not path.is_file():
        return []
    try:
        return list(json.loads(path.read_text(encoding="utf-8")))
    except (OSError, json.JSONDecodeError):
        return []


def mark_notifications_delivered(*, session_id: str) -> None:
    path = _root() / f"pending_{session_id.replace('/', '_')[:80]}.json"
    if path.is_file():
        path.unlink()


def compose_completion_message(*, job_type: str, entity_name: str | None, summary: str) -> str:
    from aethos_core.job_truth.notification_policy import compose_honest_completion_message

    return compose_honest_completion_message(
        job_type=job_type,
        entity_name=entity_name,
        summary=summary,
        last_activity_phrase="just now",
    )


def clear_job_notifications_for_tests() -> None:
    for p in _root().glob("*.json"):
        p.unlink()

# SPDX-License-Identifier: Apache-2.0
"""Execute retry intent against the active operational thread."""

from __future__ import annotations

import re
from typing import Any

_RETRY_INTENT_RX = re.compile(
    r"\b("
    r"retry(?:\s+now|\s+to\s+restart(?:\s+now)?|\s+the\s+(?:restart|redeploy|mutation))?"
    r"|try\s+again"
    r"|can\s+you\s+retry"
    r"|please\s+retry"
    r")\b",
    re.I,
)
_SIMPLE_RESTART_RX = re.compile(r"^\s*restart(?:\s+now)?\s*\.?\s*$", re.I)
_FAILED_THREAD_STATUSES = frozenset(
    {
        "execution_failed",
        "restart_unverified",
        "service_online_but_restart_unproven",
        "verification_failed",
        "failed",
        "failed_or_unverified",
    }
)


def is_retry_intent(text: str, *, session_id: str = "default") -> bool:
    raw = (text or "").strip()
    if not raw:
        return False
    if _RETRY_INTENT_RX.search(raw):
        return True
    if _SIMPLE_RESTART_RX.match(raw):
        thread = _active_retry_thread(session_id=session_id)
        return thread is not None
    return False


def compose_retry_active_operation_reply(
    text: str,
    *,
    session_id: str = "default",
) -> tuple[str, str, dict[str, str]] | None:
    if not is_retry_intent(text, session_id=session_id):
        return None

    from aethos_core.task_frame.confirmation_continuation import create_governed_retry_preflight
    from aethos_core.task_frame.pending_action import get_pending_action

    pending = get_pending_action(session_id=session_id)
    if pending is not None and pending.next_action == "create_mutation_preflight":
        return create_governed_retry_preflight(pending, session_id=session_id)

    thread = _active_retry_thread(session_id=session_id)
    if thread is None:
        return None

    from aethos_core.task_frame.pending_action import PendingAction

    action = PendingAction(
        session_id=session_id,
        provider=str(thread.provider or "railway"),
        project=str(thread.project or ""),
        environment=str(thread.environment or "production"),
        service=str(thread.service or ""),
        operation=str(thread.operation or "restart"),
        next_action="create_mutation_preflight",
        status="awaiting_user_confirmation",
    )
    return create_governed_retry_preflight(action, session_id=session_id)


def _active_retry_thread(*, session_id: str):
    from aethos_core.operational_thread_memory.thread_persistence import get_active_thread, is_thread_expired

    thread = get_active_thread(session_id=session_id)
    if thread is None or is_thread_expired(thread):
        return None
    if thread.status in {"completed", "cancelled", "superseded"}:
        return None
    if thread.status not in _FAILED_THREAD_STATUSES and thread.status not in {"preflight_created", "execution_queued", "execution_stabilizing"}:
        if thread.failure_reason:
            return thread
        return None
    return thread

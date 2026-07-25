# SPDX-License-Identifier: Apache-2.0
"""Unified outbound channel routing — registry-driven job lifecycle fan-out."""

from __future__ import annotations

import re
from time import time
from typing import Any

from aethos_core.channels.channel_registry import get_channel_adapter, resolve_adapter_for_session
from aethos_core.channels.session_identity import external_chat_id_from_session, parse_session_channel
from aethos_core.runtime.job_types import uses_operation_preflight

APPROVABLE_PREFLIGHT = frozenset({"ready_for_approval", "ready_for_readonly_diagnostic"})

_SUPPRESSED_PROGRESS = frozenset(
    {
        "resolving auth",
        "building adapter",
        "loading operational memory",
        "preparing read-only checks",
        "building evidence artifact",
        "formatting report",
        "completing execution",
    }
)

_last_progress_sent: dict[str, tuple[float, str]] = {}
_PROGRESS_COOLDOWN_SEC = 4.0


def _approval_message(job: Any) -> str | None:
    if not uses_operation_preflight(job.job_type):
        return None
    pf = job.params.get("operation_preflight") if isinstance(job.params.get("operation_preflight"), dict) else {}
    status = str(job.params.get("preflight_status") or pf.get("preflight_status") or "")
    if status not in APPROVABLE_PREFLIGHT:
        return None
    target = pf.get("target_name") or job.params.get("target_name") or "(unknown)"
    op = str(pf.get("operation_type") or job.params.get("operation_type") or "operation").replace("_", " ")
    return (
        f"⏳ Approval required — open Mission Control → Jobs to approve read-only execution.\n"
        f"Operation: {op} · Target: `{target}`"
    )


def _condense_progress_message(job: Any, message: str) -> str | None:
    raw = (message or "").strip()
    if not raw:
        return None
    lower = raw.lower()
    if lower in _SUPPRESSED_PROGRESS:
        return None
    if lower.startswith("running read-only operation preflight"):
        return "⏳ Running read-only preflight…"
    checking = re.match(r"Checking (.+?) for [`'\"]?([^`'\"]+)[`'\"]? using", raw, re.I)
    if checking:
        op = checking.group(1).strip()
        target = checking.group(2).strip()
        return f"⏳ Running read-only {op} for `{target}`…"
    if lower.startswith("fetching "):
        return f"⏳ {raw[0].upper()}{raw[1:]}…"
    if "preflight" in lower or "read-only" in lower:
        return raw if len(raw) <= 160 else raw[:160] + "…"
    return None


def _should_send_progress(job_id: str, condensed: str) -> bool:
    now = time()
    prev = _last_progress_sent.get(job_id)
    if prev:
        prev_at, prev_msg = prev
        if prev_msg == condensed:
            return False
        if now - prev_at < _PROGRESS_COOLDOWN_SEC:
            return False
    _last_progress_sent[job_id] = (now, condensed)
    return True


def clear_progress_state_for_tests() -> None:
    _last_progress_sent.clear()


def _format_outbound(job: Any, *, event_type: str, message: str, session_id: str) -> str | None:
    channel = parse_session_channel(session_id)
    if channel == "telegram":
        from aethos_core.channels.telegram.telegram_preferences import get_notify_mode

        mode = get_notify_mode(session_id=session_id)
        if mode == "completion_only" and event_type == "job_progress":
            return None

    outbound = message
    if event_type == "job_completed":
        approval = _approval_message(job)
        if approval:
            outbound = f"{approval}\n\n{message[:800]}"
    elif event_type == "job_failed":
        outbound = f"⚠️ {message[:800]}"
    elif event_type == "job_progress":
        if channel == "telegram":
            from aethos_core.channels.telegram.telegram_preferences import get_notify_mode

            mode = get_notify_mode(session_id=session_id)
            if mode != "verbose":
                condensed = _condense_progress_message(job, message)
                if not condensed:
                    return None
                job_id = str(getattr(job, "id", "") or "")
                if job_id and not _should_send_progress(job_id, condensed):
                    return None
                outbound = condensed
    return outbound[:4096] if outbound else None


def dispatch_job_lifecycle(job: Any, *, event_type: str, message: str) -> None:
    session_id = str(getattr(job, "session_id", "") or "")
    chat_id = external_chat_id_from_session(session_id)
    if not chat_id:
        return

    channel = parse_session_channel(session_id)
    if channel == "telegram":
        from aethos_core.channels.telegram.telegram_runtime import telegram_configured

        if not telegram_configured():
            return

    adapter = resolve_adapter_for_session(session_id)
    if adapter is None:
        return

    outbound = _format_outbound(job, event_type=event_type, message=message, session_id=session_id)
    if not outbound:
        return

    adapter.send_job_update(chat_id=chat_id, message=outbound)


def dispatch_job_event(*, session_id: str, message: str) -> None:
    if not message:
        return
    chat_id = external_chat_id_from_session(session_id)
    if not chat_id:
        return
    adapter = resolve_adapter_for_session(session_id)
    if adapter is None:
        return
    if parse_session_channel(session_id) == "telegram":
        from aethos_core.channels.telegram.telegram_runtime import telegram_configured

        if not telegram_configured():
            return
    adapter.send_job_update(chat_id=chat_id, message=message[:4096])

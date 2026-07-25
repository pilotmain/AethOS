# SPDX-License-Identifier: Apache-2.0
"""Deliver proactive automation results to the operator's chosen channel."""

from __future__ import annotations

from typing import Any


def deliver_automation_message(
    *,
    session_id: str,
    channel: str,
    message: str,
    title: str | None = None,
) -> dict[str, Any]:
    text = message.strip()
    if not text:
        return {"ok": False, "reason": "empty_message"}
    if title:
        text = f"**{title.strip()}**\n\n{text}"
    text = text[:4096]

    from aethos_core.jobs.job_notifications import enqueue_job_notification

    notification = enqueue_job_notification(
        session_id=session_id,
        channel=channel,
        message=text,
        job_type="automation",
    )

    live = False
    try:
        from aethos_core.channels.outbound import dispatch_job_event
        from aethos_core.channels.session_identity import external_chat_id_from_session

        if external_chat_id_from_session(session_id):
            dispatch_job_event(session_id=session_id, message=text)
            live = True
    except Exception:
        live = False

    push = None
    if (channel or "").strip().lower() in {"web", "pwa"}:
        try:
            from aethos_core.pwa.web_push import notify_tenant_web_push
            from aethos_core.tenancy import get_current_tenant

            push = notify_tenant_web_push(
                title=title or "AethOS automation",
                body=message[:500],
                url="/",
                tenant_id=get_current_tenant(),
            )
        except Exception:
            push = {"ok": False, "reason": "push_error"}

    return {
        "ok": True,
        "session_id": session_id,
        "channel": channel,
        "live_dispatch": live,
        "notification": notification,
        "web_push": push,
    }

# SPDX-License-Identifier: Apache-2.0
"""Notification pressure scoring — Phase 11.8.2."""

from __future__ import annotations

from typing import Any

from aethos_core.jobs.job_notifications import list_pending_notifications


def assess_notification_pressure(*, session_id: str = "default") -> dict[str, Any]:
    pending = list_pending_notifications(session_id=session_id)
    count = len(pending)
    pressure = "calm"
    if count >= 6:
        pressure = "high"
    elif count >= 3:
        pressure = "elevated"
    retry_msgs = sum(1 for n in pending if "retry" in str(n.get("message") or "").lower())
    return {
        "ok": True,
        "pending_count": count,
        "retry_message_count": retry_msgs,
        "notification_pressure": pressure,
        "qualified": pressure == "calm",
    }

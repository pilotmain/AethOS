# SPDX-License-Identifier: Apache-2.0
"""Notification fatigue validation — Phase 11.8.0."""

from __future__ import annotations

from typing import Any


def assess_notification_fatigue(*, session_id: str = "default") -> dict[str, Any]:
    from aethos_core.job_truth.notification_policy import compose_notification_digest
    from aethos_core.jobs.job_notifications import list_pending_notifications

    pending = list_pending_notifications(session_id=session_id)
    digest = compose_notification_digest(pending)
    grouped = len(pending) <= 1 or "Grouped" in digest or not pending
    return {
        "ok": True,
        "scenario": "notification_fatigue",
        "pending_count": len(pending),
        "notification_quality": "calm" if grouped else "noisy",
        "digest_available": bool(digest),
        "qualified": grouped,
    }

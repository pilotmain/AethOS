# SPDX-License-Identifier: Apache-2.0
"""Task frame expiration — stale pending tasks."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta


DEFAULT_TASK_TTL_MINUTES = 30


def task_expires_at(*, now: datetime | None = None, ttl_minutes: int = DEFAULT_TASK_TTL_MINUTES) -> str:
    current = now or datetime.now(UTC)
    return (current + timedelta(minutes=ttl_minutes)).isoformat()


def is_task_frame_expired(expires_at: str | None) -> bool:
    if not expires_at:
        return False
    try:
        deadline = datetime.fromisoformat(expires_at.replace("Z", "+00:00"))
    except ValueError:
        return True
    if deadline.tzinfo is None:
        deadline = deadline.replace(tzinfo=UTC)
    return datetime.now(UTC) >= deadline

# SPDX-License-Identifier: Apache-2.0
"""Conversational TTL for task-frame continuations (§1).

A pending continuation (redeploy intent, pending action, …) may only answer a
follow-up while it is genuinely recent. Beyond CONTINUATION_TTL_MINUTES it is
considered conversationally stale and must yield to the fresh turn, so an
abandoned operation never hijacks a later, unrelated request.

Time-based (wall clock) — a robust proxy for "the user has moved on" that needs
no per-session turn bookkeeping. The wider hard TTL on each store (e.g. 2h) is
unchanged; this is a tighter conversational window layered on top.
"""

from __future__ import annotations

from datetime import UTC, datetime


def continuation_ttl_minutes() -> int:
    try:
        from aethos_core.config import get_settings

        return max(1, int(getattr(get_settings(), "continuation_ttl_minutes", 30)))
    except Exception:  # noqa: BLE001 — never let TTL resolution break a turn.
        return 30


def is_frame_conversationally_stale(created_at: str | None, *, minutes: int | None = None) -> bool:
    """True when ``created_at`` is older than the conversational TTL.

    Returns ``False`` for empty/unparseable timestamps so a missing created_at
    never causes a usable frame to be dropped (the hard TTL still applies).
    """
    if not created_at:
        return False
    limit = continuation_ttl_minutes() if minutes is None else max(1, int(minutes))
    try:
        created = datetime.fromisoformat(str(created_at).replace("Z", "+00:00"))
    except ValueError:
        return False
    if created.tzinfo is None:
        created = created.replace(tzinfo=UTC)
    age_minutes = (datetime.now(UTC) - created).total_seconds() / 60.0
    return age_minutes >= limit

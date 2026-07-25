# SPDX-License-Identifier: Apache-2.0
"""Safe event poll responses — never drop the connection for read-only event lists."""

from __future__ import annotations

import logging
from collections.abc import Callable
from typing import Any

_log = logging.getLogger(__name__)


def safe_event_poll(fetch_events: Callable[[], list[dict[str, Any]]]) -> dict[str, Any]:
    try:
        events = fetch_events()
        return {"ok": True, "events": events, "count": len(events)}
    except Exception as exc:
        _log.exception("event_poll_failed")
        return {
            "ok": False,
            "events": [],
            "count": 0,
            "error": {
                "code": "EVENT_POLL_FAILED",
                "detail": str(exc)[:240],
            },
        }

# SPDX-License-Identifier: Apache-2.0
"""In-process Mission Control live update bus — SSE fan-out for deploy/approval events."""

from __future__ import annotations

import json
import threading
import uuid
from collections import deque
from datetime import UTC, datetime
from typing import Any, Iterator

_LOCK = threading.Lock()
_RECENT: deque[dict[str, Any]] = deque(maxlen=200)
_SUBSCRIBERS: list[deque[dict[str, Any]]] = []


def publish_live_update(*, event_type: str, payload: dict[str, Any] | None = None) -> dict[str, Any]:
    event = {
        "id": uuid.uuid4().hex,
        "type": event_type,
        "timestamp": datetime.now(UTC).isoformat(),
        "payload": dict(payload or {}),
    }
    with _LOCK:
        _RECENT.append(event)
        for queue in _SUBSCRIBERS:
            queue.append(event)
    return event


def recent_live_updates(*, limit: int = 50) -> list[dict[str, Any]]:
    with _LOCK:
        rows = list(_RECENT)
    return rows[-limit:]


def subscribe_live_updates() -> Iterator[dict[str, Any]]:
    queue: deque[dict[str, Any]] = deque()
    with _LOCK:
        _SUBSCRIBERS.append(queue)
    try:
        while True:
            if queue:
                yield queue.popleft()
            else:
                yield {"type": "heartbeat", "timestamp": datetime.now(UTC).isoformat(), "payload": {}}
                threading.Event().wait(15.0)
    finally:
        with _LOCK:
            if queue in _SUBSCRIBERS:
                _SUBSCRIBERS.remove(queue)


def sse_stream(*, replay: int = 20) -> Iterator[str]:
    for row in recent_live_updates(limit=replay):
        yield f"data: {json.dumps(row, ensure_ascii=False)}\n\n"
    for event in subscribe_live_updates():
        yield f"data: {json.dumps(event, ensure_ascii=False)}\n\n"


def reset_live_update_bus_for_tests() -> None:
    with _LOCK:
        _RECENT.clear()
        _SUBSCRIBERS.clear()

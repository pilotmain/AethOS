# SPDX-License-Identifier: Apache-2.0
"""Telegram outbound delivery — retries and lightweight queue."""

from __future__ import annotations

import logging
import threading
import time
from dataclasses import dataclass, field
from typing import Any

_log = logging.getLogger(__name__)

MAX_ATTEMPTS = 3
RETRY_BACKOFF_SEC = (1.0, 2.0, 4.0)


@dataclass
class _QueuedDelivery:
    token: str
    chat_id: str
    text: str
    attempts: int = 0
    enqueued_at: float = field(default_factory=time.time)
    last_error: str = ""


_queue: list[_QueuedDelivery] = []
_lock = threading.Lock()
_retry_count = 0
_retry_success_count = 0


def _is_retryable(detail: str, status_code: int = 0) -> bool:
    d = (detail or "").lower()
    if status_code == 429 or "too many requests" in d or "retry after" in d:
        return True
    if status_code in (502, 503, 504):
        return True
    return any(x in d for x in ("timeout", "timed out", "connection reset", "connection refused"))


def queue_snapshot() -> dict[str, Any]:
    with _lock:
        return {
            "queued": len(_queue),
            "retry_attempts": _retry_count,
            "retry_successes": _retry_success_count,
        }


def clear_for_tests() -> None:
    global _retry_count, _retry_success_count
    with _lock:
        _queue.clear()
    _retry_count = 0
    _retry_success_count = 0


def deliver_message(*, token: str, chat_id: str, text: str, bot_api_fn) -> dict[str, Any]:
    """Send with inline retries; enqueue for background retry on persistent failure."""
    last_detail = ""
    last_status = 0
    for attempt in range(MAX_ATTEMPTS):
        out = bot_api_fn(token=token, method="sendMessage", payload={"chat_id": chat_id, "text": text[:4096]})
        if out.get("ok"):
            return {"ok": True, "detail": str(out.get("detail") or "ok")}
        last_detail = str(out.get("detail") or "")
        last_status = int(out.get("status_code") or 0)
        if attempt + 1 < MAX_ATTEMPTS and _is_retryable(last_detail, last_status):
            global _retry_count
            _retry_count += 1
            time.sleep(RETRY_BACKOFF_SEC[min(attempt, len(RETRY_BACKOFF_SEC) - 1)])
            continue
        break

    with _lock:
        _queue.append(
            _QueuedDelivery(
                token=token,
                chat_id=chat_id,
                text=text[:4096],
                attempts=MAX_ATTEMPTS,
                last_error=last_detail[:200],
            )
        )
    _log.warning("telegram_delivery_queued chat=%s err=%s", chat_id, last_detail[:120])
    return {"ok": False, "detail": last_detail or "send_failed", "status_code": last_status}


def flush_queue(*, bot_api_fn, limit: int = 10) -> dict[str, int]:
    """Process queued deliveries — call from status endpoint or worker tick."""
    global _retry_success_count
    sent = 0
    failed = 0
    remaining: list[_QueuedDelivery] = []
    with _lock:
        batch = _queue[:limit]
        del _queue[:limit]

    for item in batch:
        out = bot_api_fn(
            token=item.token,
            method="sendMessage",
            payload={"chat_id": item.chat_id, "text": item.text},
        )
        if out.get("ok"):
            sent += 1
            _retry_success_count += 1
        else:
            item.attempts += 1
            item.last_error = str(out.get("detail") or "")[:200]
            if item.attempts < MAX_ATTEMPTS + 2:
                remaining.append(item)
            failed += 1

    if remaining:
        with _lock:
            _queue[:0] = remaining
    return {"sent": sent, "failed": failed, "queued": len(_queue)}

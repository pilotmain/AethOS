# SPDX-License-Identifier: Apache-2.0
"""Telegram sendChatAction — typing indicator with rate limiting."""

from __future__ import annotations

import asyncio
import logging
import threading
import time
from typing import Any

from aethos_core.config import get_settings
from aethos_core.security.secret_redaction import redact_text

_log = logging.getLogger(__name__)

_last_typing_sent_at: float | None = None
_last_typing_error: str | None = None
_typing_send_count = 0
_typing_lock = threading.Lock()


def typing_diagnostics() -> dict[str, Any]:
    s = get_settings()
    with _typing_lock:
        return {
            "typing_enabled": bool(s.telegram_typing_enabled),
            "progress_messages_enabled": bool(s.telegram_progress_message_enabled),
            "typing_interval_seconds": int(s.telegram_typing_interval_seconds),
            "progress_after_seconds": int(s.telegram_progress_after_seconds),
            "last_typing_sent_at": _last_typing_sent_at,
            "last_typing_error": _last_typing_error,
            "typing_send_count": _typing_send_count,
        }


def clear_typing_diagnostics_for_tests() -> None:
    global _last_typing_sent_at, _last_typing_error, _typing_send_count
    with _typing_lock:
        _last_typing_sent_at = None
        _last_typing_error = None
        _typing_send_count = 0


def _record_typing_result(*, ok: bool, detail: str = "") -> None:
    global _last_typing_sent_at, _last_typing_error, _typing_send_count
    with _typing_lock:
        _typing_send_count += 1
        if ok:
            _last_typing_sent_at = time.time()
            _last_typing_error = None
        else:
            _last_typing_error = redact_text(detail)[:240] or "typing_failed"


def send_chat_action_sync(*, token: str, chat_id: str, action: str = "typing") -> bool:
    if not token or not chat_id:
        _record_typing_result(ok=False, detail="missing token or chat_id")
        return False
    from aethos_core.channels.telegram.telegram_transport import _bot_api

    out = _bot_api(token=token, method="sendChatAction", payload={"chat_id": chat_id, "action": action})
    ok = bool(out.get("ok"))
    if not ok:
        detail = str(out.get("detail") or "sendChatAction failed")
        _log.warning("telegram_typing_failed chat=%s detail=%s", chat_id, detail[:120])
        _record_typing_result(ok=False, detail=detail)
    else:
        _record_typing_result(ok=True)
    return ok


async def send_typing(chat_id: str) -> None:
    s = get_settings()
    if not s.telegram_typing_enabled:
        return
    from aethos_core.channels.telegram.telegram_token import resolve_telegram_bot_token

    token, _ = resolve_telegram_bot_token()
    if not token:
        _record_typing_result(ok=False, detail="telegram token missing")
        return
    await asyncio.to_thread(send_chat_action_sync, token=token, chat_id=chat_id, action="typing")


async def typing_loop(chat_id: str, stop_event: asyncio.Event, interval_seconds: int | None = None) -> None:
    s = get_settings()
    if not s.telegram_typing_enabled:
        return
    interval = max(2, int(interval_seconds or s.telegram_typing_interval_seconds))
    await send_typing(chat_id)
    while not stop_event.is_set():
        try:
            await asyncio.wait_for(stop_event.wait(), timeout=interval)
            break
        except asyncio.TimeoutError:
            if stop_event.is_set():
                break
            await send_typing(chat_id)


class TelegramProgressMirror:
    """§4 — mirror live tool-loop progress to a single editable Telegram message.

    Read-only visibility only: it narrates what the agent tool loop reports and
    never executes anything. One message per turn, rate-limited to the typing
    interval, and deferred until the turn has been working for
    ``telegram_progress_after_seconds`` so quick replies stay spam-free. Every
    line is run through secret redaction before it leaves the process.
    """

    def __init__(self, *, token: str, chat_id: str) -> None:
        s = get_settings()
        self._token = token
        self._chat_id = chat_id
        self._after = max(0, int(s.telegram_progress_after_seconds))
        self._interval = max(2, int(s.telegram_typing_interval_seconds))
        self._started = time.monotonic()
        self._message_id: int | None = None
        self._last_edit = 0.0
        self._last_text = ""
        self._steps = 0
        self._lock = threading.Lock()

    @staticmethod
    def _line(ev: dict[str, Any]) -> str:
        if ev.get("type") == "thought":
            return redact_text(str(ev.get("text") or "").strip())
        if str(ev.get("status") or "") == "running":
            return redact_text(str(ev.get("action") or "Working").strip())
        return redact_text(str(ev.get("summary") or ev.get("action") or "Done").strip())

    def on_event(self, ev: dict[str, Any]) -> None:
        from aethos_core.channels.telegram.telegram_transport import _bot_api

        try:
            if ev.get("type") == "step" and ev.get("status") == "running":
                self._steps += 1
            line = self._line(ev)
            if not line:
                return
            now = time.monotonic()
            text = f"🔧 Working… {line}"[:300]
            with self._lock:
                if self._message_id is None:
                    if (now - self._started) < self._after:
                        return  # too early — keep quiet for quick turns
                    out = _bot_api(
                        token=self._token,
                        method="sendMessage",
                        payload={"chat_id": self._chat_id, "text": text},
                    )
                    res = out.get("result") if isinstance(out.get("result"), dict) else {}
                    self._message_id = res.get("message_id")
                    self._last_edit = now
                    self._last_text = text
                    return
                if text == self._last_text or (now - self._last_edit) < self._interval:
                    return
                _bot_api(
                    token=self._token,
                    method="editMessageText",
                    payload={"chat_id": self._chat_id, "message_id": self._message_id, "text": text},
                )
                self._last_edit = now
                self._last_text = text
        except Exception:  # noqa: BLE001 — narration must never break the turn.
            pass

    def finish(self) -> None:
        from aethos_core.channels.telegram.telegram_transport import _bot_api

        try:
            with self._lock:
                if self._message_id is None:
                    return
                plural = "" if self._steps == 1 else "s"
                _bot_api(
                    token=self._token,
                    method="editMessageText",
                    payload={
                        "chat_id": self._chat_id,
                        "message_id": self._message_id,
                        "text": f"✓ Worked through {self._steps} step{plural}.",
                    },
                )
        except Exception:  # noqa: BLE001
            pass


def typing_loop_sync(
    chat_id: str,
    stop_event: threading.Event,
    interval_seconds: int | None = None,
    token: str | None = None,
) -> None:
    s = get_settings()
    if not s.telegram_typing_enabled:
        return
    # The caller (request thread) resolves the bot token under the authenticated
    # tenant scope and passes it in. We must NOT re-resolve here: this runs in a
    # daemon thread that does not inherit the request's tenant contextvar, so a
    # vault-stored (tenant-scoped) token would come back empty and typing would
    # silently no-op. Only fall back to resolving when no token was provided.
    if not token:
        from aethos_core.channels.telegram.telegram_token import resolve_telegram_bot_token

        token, _ = resolve_telegram_bot_token()
    if not token:
        _record_typing_result(ok=False, detail="telegram token missing")
        return
    interval = max(2, int(interval_seconds or s.telegram_typing_interval_seconds))
    send_chat_action_sync(token=token, chat_id=chat_id, action="typing")
    while not stop_event.wait(timeout=interval):
        if stop_event.is_set():
            break
        send_chat_action_sync(token=token, chat_id=chat_id, action="typing")

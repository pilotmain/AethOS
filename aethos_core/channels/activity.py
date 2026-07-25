# SPDX-License-Identifier: Apache-2.0
"""Channel activity adapters — typing/progress for transports."""

from __future__ import annotations

import asyncio
import logging
import threading
import time
from typing import Any, Protocol

from aethos_core.config import get_settings

_log = logging.getLogger(__name__)

PROGRESS_COPY: dict[str, str] = {
    "research": "AethOS is researching live sources and building an evidence summary...",
    "browser_evidence": "AethOS is capturing browser evidence and storing artifacts...",
    "multi_agent": "AethOS is coordinating specialist agents and merging evidence...",
    "engineering": "AethOS is preparing a governed engineering preflight...",
    "provider_readonly": "AethOS is checking provider evidence...",
    "mutation_preflight": "AethOS is preparing mutation preflight...",
    "operational_grounding": "AethOS is reconstructing operational continuity and runtime truth...",
    "default_chat": "AethOS is thinking...",
}


def infer_channel_activity_type(text: str) -> str:
    raw = (text or "").strip()
    if not raw:
        return "default_chat"

    from aethos_core.browser.runtime.browser_evidence_intents import is_browser_evidence_request

    if is_browser_evidence_request(raw):
        return "browser_evidence"

    from aethos_core.chat.web_intelligence import is_web_intelligence_request

    if is_web_intelligence_request(raw):
        return "research"

    from aethos_core.chat.engineering_intelligence import is_engineering_intelligence_request

    if is_engineering_intelligence_request(raw):
        return "engineering"

    from aethos_core.agents.runtime.planner import is_multi_agent_request

    if is_multi_agent_request(raw):
        return "multi_agent"

    from aethos_core.chat.mutation_preflight_prompts import create_mutation_preflight_job_reply

    if create_mutation_preflight_job_reply(raw) is not None:
        return "mutation_preflight"

    from aethos_core.chat.railway_readonly_prompts import create_railway_readonly_job_reply
    from aethos_core.chat.github_readonly_prompts import create_github_readonly_job_reply

    if create_railway_readonly_job_reply(raw) is not None or create_github_readonly_job_reply(raw) is not None:
        return "provider_readonly"

    from aethos_core.continuity_reconstruction.prompt_inference import infer_continuity_intent

    if infer_continuity_intent(raw).get("continuity_prompt"):
        return "operational_grounding"

    return "default_chat"


def progress_message_for_activity(activity_type: str) -> str:
    return PROGRESS_COPY.get(activity_type, PROGRESS_COPY["default_chat"])


class ChannelActivityAdapter(Protocol):
    async def start_activity(self, session_id: str, activity_type: str, *, chat_id: str = "") -> None: ...

    async def stop_activity(self, session_id: str) -> None: ...

    async def send_progress(self, session_id: str, message: str, *, chat_id: str = "") -> None: ...


class NoOpChannelActivityAdapter:
    async def start_activity(self, session_id: str, activity_type: str, *, chat_id: str = "") -> None:
        return None

    async def stop_activity(self, session_id: str) -> None:
        return None

    async def send_progress(self, session_id: str, message: str, *, chat_id: str = "") -> None:
        return None


class TelegramChannelActivityAdapter:
    def __init__(self) -> None:
        self._stop_events: dict[str, asyncio.Event] = {}
        self._typing_tasks: dict[str, asyncio.Task[Any]] = {}
        self._progress_sent: set[str] = set()

    async def start_activity(self, session_id: str, activity_type: str, *, chat_id: str = "") -> None:
        if not chat_id:
            return
        from aethos_core.channels.telegram.chat_action import send_typing, typing_loop

        stop = asyncio.Event()
        self._stop_events[session_id] = stop
        self._typing_tasks[session_id] = asyncio.create_task(typing_loop(chat_id, stop))

    async def stop_activity(self, session_id: str) -> None:
        stop = self._stop_events.pop(session_id, None)
        task = self._typing_tasks.pop(session_id, None)
        if stop:
            stop.set()
        if task:
            task.cancel()
            try:
                await task
            except asyncio.CancelledError:
                pass

    async def send_progress(self, session_id: str, message: str, *, chat_id: str = "") -> None:
        if not chat_id or session_id in self._progress_sent:
            return
        s = get_settings()
        if not s.telegram_progress_message_enabled:
            return
        from aethos_core.channels.telegram.telegram_token import resolve_telegram_bot_token
        from aethos_core.channels.telegram.telegram_transport import send_telegram_message

        token, _ = resolve_telegram_bot_token()
        if not token:
            return
        out = await asyncio.to_thread(
            send_telegram_message,
            token=token,
            chat_id=chat_id,
            text=message,
        )
        if isinstance(out, dict) and out.get("ok"):
            self._progress_sent.add(session_id)


class TelegramActivitySession:
    """Sync activity session for webhook handler (thread-based typing + progress)."""

    def __init__(self, *, chat_id: str, session_id: str, activity_type: str, token: str = "") -> None:
        self.chat_id = chat_id
        self.session_id = session_id
        self.activity_type = activity_type
        # Resolved by the request thread under the tenant scope; threaded into the
        # daemon typing/progress threads so they don't re-resolve without it.
        self.token = token
        self._stop = threading.Event()
        self._done = threading.Event()
        self._progress_sent = threading.Event()
        self._typing_thread: threading.Thread | None = None
        self._progress_thread: threading.Thread | None = None

    def __enter__(self) -> TelegramActivitySession:
        s = get_settings()
        if s.telegram_typing_enabled and self.chat_id:
            from aethos_core.channels.telegram.chat_action import typing_loop_sync

            self._typing_thread = threading.Thread(
                target=typing_loop_sync,
                args=(self.chat_id, self._stop, None, self.token or None),
                daemon=True,
                name=f"tg-typing-{self.session_id[:12]}",
            )
            self._typing_thread.start()
        if s.telegram_progress_message_enabled and self.chat_id:
            self._progress_thread = threading.Thread(
                target=self._progress_worker,
                daemon=True,
                name=f"tg-progress-{self.session_id[:12]}",
            )
            self._progress_thread.start()
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        self._done.set()
        self._stop.set()
        if self._typing_thread and self._typing_thread.is_alive():
            self._typing_thread.join(timeout=1.5)
        if self._progress_thread and self._progress_thread.is_alive():
            self._progress_thread.join(timeout=1.5)

    def _progress_worker(self) -> None:
        s = get_settings()
        delay = max(3, int(s.telegram_progress_after_seconds))
        if self._done.wait(timeout=delay):
            return
        if self._progress_sent.is_set() or self._done.is_set():
            return
        message = progress_message_for_activity(self.activity_type)
        try:
            from aethos_core.channels.telegram.telegram_transport import send_telegram_message

            token = self.token
            if not token:
                from aethos_core.channels.telegram.telegram_token import resolve_telegram_bot_token

                token, _ = resolve_telegram_bot_token()
            if token:
                out = send_telegram_message(token=token, chat_id=self.chat_id, text=message)
                if isinstance(out, dict) and out.get("ok"):
                    self._progress_sent.set()
        except Exception as exc:
            _log.warning("telegram_progress_failed session=%s err=%s", self.session_id, exc.__class__.__name__)


def get_channel_activity_adapter(channel: str) -> ChannelActivityAdapter:
    if channel == "telegram":
        return TelegramChannelActivityAdapter()
    return NoOpChannelActivityAdapter()


def telegram_activity_session(
    *, chat_id: str, session_id: str, user_text: str, token: str = ""
) -> TelegramActivitySession:
    activity_type = infer_channel_activity_type(user_text)
    return TelegramActivitySession(
        chat_id=chat_id, session_id=session_id, activity_type=activity_type, token=token
    )

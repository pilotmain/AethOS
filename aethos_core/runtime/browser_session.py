# SPDX-License-Identifier: Apache-2.0
"""Supervised browser session registry — lifecycle, events, heartbeats."""

from __future__ import annotations

import threading
from dataclasses import dataclass, field
from time import time
from typing import Any
from uuid import uuid4

from aethos_core.config import get_settings
from aethos_core.runtime.authority import authority
from aethos_core.runtime.browser_diagnostics import validate_browser_runtime_for_execution
from aethos_core.runtime.browser_driver import DriverHandle, get_browser_driver
from aethos_core.runtime.browser_lifecycle import (
    ACTIVE_STATUSES,
    BrowserSessionStatus,
    TERMINAL_STATUSES,
    chat_message_for_session_event,
)


def normalize_target_url(target: str) -> str:
    raw = (target or "").strip()
    if not raw or raw == "unknown":
        return "https://vercel.com"
    if raw.startswith("http://") or raw.startswith("https://"):
        return raw
    return f"https://{raw}"


def _new_session_id() -> str:
    return f"bsess-{uuid4().hex[:12]}"


def _event_id(session_id: str, event_type: str, suffix: str = "") -> str:
    if suffix:
        return f"{session_id}:{event_type}:{suffix}"
    return f"{session_id}:{event_type}"


def _browser_pid_from_handle(handle: DriverHandle | None) -> int | None:
    if handle is None or handle.browser is None:
        return None
    proc = getattr(handle.browser, "process", None)
    if proc is None:
        return None
    pid = getattr(proc, "pid", None)
    return int(pid) if isinstance(pid, int) else None


@dataclass
class BrowserSessionEvent:
    id: str
    session_id: str
    event_type: str
    message: str
    status: str
    target: str
    chat_session_id: str
    at: float = field(default_factory=time)

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "event_id": self.id,
            "session_id": self.session_id,
            "event_type": self.event_type,
            "message": self.message,
            "status": self.status,
            "target": self.target,
            "session_id_chat": self.chat_session_id,
            "chat_session_id": self.chat_session_id,
            "at": self.at,
            "created_at": self.at,
        }


@dataclass
class BrowserSession:
    id: str
    target: str
    url: str
    status: BrowserSessionStatus
    mode: str = "supervised"
    action_id: str | None = None
    chat_session_id: str = "default"
    operator_approved: bool = True
    login_notice: bool = False
    created_at: float = field(default_factory=time)
    updated_at: float = field(default_factory=time)
    started_at: float | None = None
    last_heartbeat: float = field(default_factory=time)
    browser_pid: int | None = None
    error: str | None = None
    persistence_status: str = "none"
    persistence_last_attempt_at: float | None = None
    persistence_last_error: str | None = None
    _handle: DriverHandle | None = field(default=None, repr=False)

    def to_dict(self) -> dict[str, Any]:
        now = time()
        duration_sec = None
        if self.started_at is not None and self.status in ACTIVE_STATUSES:
            duration_sec = round(now - self.started_at, 1)
        elif self.started_at is not None and self.status in TERMINAL_STATUSES:
            duration_sec = round((self.updated_at or now) - self.started_at, 1)
        heartbeat_age_sec = round(now - self.last_heartbeat, 1) if self.last_heartbeat else None
        profile_save_eligible = self.status in ACTIVE_STATUSES and self._handle is not None
        return {
            "id": self.id,
            "target": self.target,
            "url": self.url,
            "status": self.status.value,
            "mode": self.mode,
            "action_id": self.action_id,
            "chat_session_id": self.chat_session_id,
            "operator_approved": self.operator_approved,
            "login_notice": self.login_notice,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "started_at": self.started_at,
            "last_heartbeat": self.last_heartbeat,
            "heartbeat_age_sec": heartbeat_age_sec,
            "browser_pid": self.browser_pid,
            "duration_sec": duration_sec,
            "error": self.error,
            "profile_save_eligible": profile_save_eligible,
            "storage_state_available": profile_save_eligible,
            "persistence_status": self.persistence_status,
            "persistence_last_attempt_at": self.persistence_last_attempt_at,
            "persistence_last_error": self.persistence_last_error,
        }


class BrowserSessionStore:
    """Thread-safe supervised browser sessions with lifecycle events."""

    def __init__(self) -> None:
        self._sessions: dict[str, BrowserSession] = {}
        self._events: list[BrowserSessionEvent] = []
        self._lock = threading.Lock()

    def _touch(self, session: BrowserSession) -> None:
        session.updated_at = time()

    def _emit(
        self,
        session: BrowserSession,
        event_type: str,
        *,
        suffix: str = "",
    ) -> BrowserSessionEvent:
        eid = _event_id(session.id, event_type, suffix)
        for existing in self._events:
            if existing.id == eid:
                return existing
        event = BrowserSessionEvent(
            id=eid,
            session_id=session.id,
            event_type=event_type,
            message=chat_message_for_session_event(
                event_type=event_type,
                target=session.target,
                status=session.status.value,
            ),
            status=session.status.value,
            target=session.target,
            chat_session_id=session.chat_session_id,
        )
        self._events.append(event)
        return event

    def get(self, session_id: str) -> BrowserSession | None:
        with self._lock:
            return self._sessions.get(session_id)

    def list_all(self) -> list[BrowserSession]:
        with self._lock:
            return sorted(self._sessions.values(), key=lambda s: s.created_at, reverse=True)

    def list_events(
        self,
        *,
        session_ids: list[str] | None = None,
        session_id: str | None = None,
        chat_session_id: str | None = None,
        since: float = 0.0,
        since_event_id: str | None = None,
    ) -> list[dict[str, Any]]:
        id_set = set(session_ids) if session_ids else None
        start_idx = 0
        if since_event_id:
            for i, event in enumerate(self._events):
                if event.id == since_event_id:
                    start_idx = i + 1
                    break
        out: list[BrowserSessionEvent] = []
        for event in self._events[start_idx:]:
            if event.at < since:
                continue
            if id_set is not None and event.session_id not in id_set:
                continue
            if id_set is None and session_id and event.session_id != session_id:
                continue
            if id_set is None and chat_session_id and event.chat_session_id != chat_session_id:
                continue
            out.append(event)
        out.sort(key=lambda e: e.at)
        return [e.to_dict() for e in out]

    def active_sessions(self) -> list[BrowserSession]:
        with self._lock:
            return [s for s in self._sessions.values() if s.status in ACTIVE_STATUSES]

    def active_session(self) -> BrowserSession | None:
        active = self.active_sessions()
        return active[0] if active else None

    def active_count(self) -> int:
        return len(self.active_sessions())

    def prepare_approved_launch(
        self,
        *,
        target: str,
        action_id: str,
        chat_session_id: str,
        login_notice: bool = False,
    ) -> BrowserSession:
        get_settings()
        if not authority.capabilities.get("browser_automation_enabled"):
            raise RuntimeError(
                "Browser automation is disabled. Enable BROWSER_AUTOMATION_ENABLED=true and restart AethOS."
            )
        validate_browser_runtime_for_execution()

        url = normalize_target_url(target)
        with self._lock:
            self._close_active_locked()
            session = BrowserSession(
                id=_new_session_id(),
                target=target,
                url=url,
                status=BrowserSessionStatus.QUEUED,
                action_id=action_id,
                chat_session_id=chat_session_id,
                operator_approved=True,
                login_notice=login_notice,
            )
            session.status = BrowserSessionStatus.APPROVED
            self._sessions[session.id] = session
            self._touch(session)
            self._emit(session, "session_approved")
        return session

    def enqueue_launch(self, session_id: str) -> None:
        from aethos_core.runtime.browser_executor import browser_executor

        with self._lock:
            session = self._sessions.get(session_id)
            if not session:
                raise KeyError(session_id)
            session.status = BrowserSessionStatus.LAUNCHING
            self._touch(session)
            self._emit(session, "session_launching")
        browser_executor.enqueue(session_id)

    def launch_session_worker(self, session_id: str) -> None:
        """Runs on browser executor thread only."""
        try:
            self._launch_locked(session_id)
        except Exception as exc:
            self._fail_launch(session_id, str(exc))

    def _launch_locked(self, session_id: str) -> None:
        s = get_settings()
        with self._lock:
            session = self._sessions.get(session_id)
            if not session or session.status in TERMINAL_STATUSES:
                return
            if session.status != BrowserSessionStatus.LAUNCHING:
                session.status = BrowserSessionStatus.LAUNCHING
            url = session.url
            headless = s.browser_headless
            login_notice = session.login_notice
            action_id = session.action_id
            target = session.target

        driver = get_browser_driver()
        handle = driver.open_url(url, headless=headless)
        now = time()
        terminal_status = (
            BrowserSessionStatus.WAITING_FOR_OPERATOR
            if login_notice
            else BrowserSessionStatus.RUNNING
        )
        event_type = (
            "session_waiting_for_operator"
            if login_notice
            else "session_running"
        )

        with self._lock:
            session = self._sessions.get(session_id)
            if not session:
                driver.close_handle(handle)
                return
            session._handle = handle
            session.status = terminal_status
            session.started_at = now
            session.last_heartbeat = now
            session.browser_pid = _browser_pid_from_handle(handle)
            self._touch(session)
            self._emit(session, event_type)

        if action_id:
            from aethos_core.runtime.actions import action_store

            action_store.complete_browser_launch(
                action_id,
                success=True,
                session_id=session_id,
                session_status=terminal_status.value,
                target=target,
                login_notice=login_notice,
            )

    def _fail_launch(self, session_id: str, error: str) -> None:
        action_id: str | None = None
        target = "unknown"
        with self._lock:
            session = self._sessions.get(session_id)
            if not session:
                return
            action_id = session.action_id
            target = session.target
            session.status = BrowserSessionStatus.FAILED
            session.error = error
            self._touch(session)
            self._emit(session, "session_failed")

        if action_id:
            from aethos_core.runtime.actions import action_store

            action_store.complete_browser_launch(
                action_id,
                success=False,
                error=error,
                target=target,
            )

    def tick_heartbeats(self) -> None:
        now = time()
        with self._lock:
            for session in self._sessions.values():
                if session.status in ACTIVE_STATUSES:
                    session.last_heartbeat = now
                    self._touch(session)

    def cleanup_stale_sessions(self) -> None:
        s = get_settings()
        stale_after = s.browser_heartbeat_stale_sec
        now = time()
        stale_ids: list[str] = []
        with self._lock:
            for session in self._sessions.values():
                if session.status not in ACTIVE_STATUSES:
                    continue
                if now - session.last_heartbeat > stale_after:
                    stale_ids.append(session.id)
        for sid in stale_ids:
            self.terminate(sid, reason="heartbeat stale")

    def cancel(self, session_id: str) -> BrowserSession:
        with self._lock:
            session = self._sessions.get(session_id)
            if not session:
                raise KeyError(session_id)
            if session.status in TERMINAL_STATUSES:
                return session
            if session.status == BrowserSessionStatus.LAUNCHING:
                session.status = BrowserSessionStatus.CANCELLED
                session.error = "Cancelled while launching"
                self._touch(session)
                self._emit(session, "session_cancelled")
                return session
            if session._handle is not None:
                get_browser_driver().close_handle(session._handle)
                session._handle = None
            session.status = BrowserSessionStatus.CANCELLED
            self._touch(session)
            self._emit(session, "session_cancelled")
            return session

    def terminate(self, session_id: str, *, reason: str = "operator terminate") -> BrowserSession:
        with self._lock:
            session = self._sessions.get(session_id)
            if not session:
                raise KeyError(session_id)
            if session.status in TERMINAL_STATUSES:
                return session
            if session._handle is not None:
                get_browser_driver().close_handle(session._handle)
                session._handle = None
            if session.status == BrowserSessionStatus.LAUNCHING:
                session.status = BrowserSessionStatus.CANCELLED
                session.error = reason
                self._touch(session)
                self._emit(session, "session_cancelled")
                return session
            if "stale" in reason.lower() or "timed out" in reason.lower():
                session.status = BrowserSessionStatus.TIMED_OUT
                session.error = reason
                self._touch(session)
                self._emit(session, "session_timed_out")
                return session
            session.status = BrowserSessionStatus.COMPLETED
            session.error = reason if reason != "operator terminate" else None
            self._touch(session)
            self._emit(session, "session_completed")
            return session

    def can_save_profile(self, session_id: str) -> bool:
        with self._lock:
            session = self._sessions.get(session_id)
            return bool(
                session
                and session.status in ACTIVE_STATUSES
                and session._handle is not None
            )

    def save_profile_from_session(
        self,
        session_id: str,
        *,
        persistence_mode: str = "use_once",
    ) -> dict[str, Any]:
        """Explicit opt-in — Playwright export runs on browser executor thread only."""
        from aethos_core.runtime.browser_runtime import run_browser_sync

        return run_browser_sync(
            lambda: self._save_profile_from_session_on_browser_thread(
                session_id,
                persistence_mode=persistence_mode,
            ),
            timeout=90.0,
        )

    def _save_profile_from_session_on_browser_thread(
        self,
        session_id: str,
        *,
        persistence_mode: str = "use_once",
    ) -> dict[str, Any]:
        from aethos_core.runtime.browser_profile_errors import BrowserProfileSaveError
        from aethos_core.runtime.browser_profile_store import browser_profile_store
        from aethos_core.runtime.vercel_readonly_inspector import export_storage_from_session_handle

        sid = (session_id or "").strip()
        if not sid:
            raise BrowserProfileSaveError(
                "MISSING_SESSION_ID",
                "Save failed — missing session id.",
                http_status=400,
            )

        existing = browser_profile_store.find_by_source_session(sid)
        if existing:
            return existing.to_public_dict()

        with self._lock:
            session = self._sessions.get(sid)
            if not session:
                raise BrowserProfileSaveError(
                    "SESSION_NOT_FOUND",
                    "Save failed — browser session not found.",
                    http_status=404,
                )
            if session.status not in ACTIVE_STATUSES:
                raise BrowserProfileSaveError(
                    "SESSION_NOT_ACTIVE",
                    "Save failed — browser session expired before persistence.",
                    http_status=409,
                )
            if session._handle is None:
                raise BrowserProfileSaveError(
                    "SESSION_NOT_ACTIVE",
                    "Save failed — browser context is no longer active.",
                    http_status=409,
                )
            handle = session._handle
            site = session.target
            session.persistence_last_attempt_at = time()
            session.persistence_last_error = None

        try:
            state = export_storage_from_session_handle(handle)
        except Exception as exc:
            with self._lock:
                s = self._sessions.get(sid)
                if s:
                    s.persistence_last_error = str(exc)
            raise BrowserProfileSaveError(
                "STORAGE_EXPORT_FAILED",
                f"Save failed — unable to persist Playwright state ({exc}).",
                http_status=422,
            ) from exc

        if not state or (
            not state.get("mock")
            and not state.get("cookies")
            and not state.get("origins")
        ):
            raise BrowserProfileSaveError(
                "STORAGE_STATE_EMPTY",
                "Save failed — no session cookies/state to persist. Log in in the browser first.",
                http_status=422,
            )

        try:
            profile = browser_profile_store.save_from_session(
                session_id=sid,
                site=site,
                storage_state=state,
                persistence_mode=persistence_mode,
            )
        except Exception as exc:
            with self._lock:
                s = self._sessions.get(sid)
                if s:
                    s.persistence_last_error = str(exc)
            raise BrowserProfileSaveError(
                "PERSISTENCE_WRITE_FAILED",
                f"Save failed — could not write profile ({exc}).",
                http_status=500,
            ) from exc

        with self._lock:
            s = self._sessions.get(sid)
            if s:
                s.persistence_status = "saved"
                s.persistence_last_error = None
        return profile.to_public_dict()

    def close(self, session_id: str) -> BrowserSession:
        return self.terminate(session_id, reason="closed")

    def close_all(self) -> None:
        with self._lock:
            ids = list(self._sessions.keys())
        for sid in ids:
            try:
                with self._lock:
                    s = self._sessions.get(sid)
                    if s and s.status in ACTIVE_STATUSES:
                        if s._handle is not None:
                            get_browser_driver().close_handle(s._handle)
                            s._handle = None
                        s.status = BrowserSessionStatus.COMPLETED
                        self._touch(s)
            except Exception:
                pass

    def _close_active_locked(self) -> None:
        for session in list(self._sessions.values()):
            if session.status in ACTIVE_STATUSES:
                if session._handle is not None:
                    get_browser_driver().close_handle(session._handle)
                    session._handle = None
                session.status = BrowserSessionStatus.COMPLETED
                self._touch(session)
                self._emit(session, "session_completed", suffix="superseded")

    def execute_approved_browser_action(
        self,
        action_type: str,
        params: dict[str, Any],
        *,
        action_id: str | None = None,
        chat_session_id: str = "default",
    ) -> tuple[str, dict[str, Any]]:
        target = str(params.get("target") or "vercel.com")
        extra: dict[str, Any] = {}

        if action_type == "browser_status_check":
            from aethos_core.runtime.browser_capability import get_browser_capability_status

            cap = get_browser_capability_status()
            lines = [
                "Browser status check (no session opened).",
                f"- Foundation: {cap.get('foundation_label')}",
                f"- Execution: {cap.get('execution_label')}",
                f"- Playwright package: {cap.get('playwright_package')}",
                f"- Chromium: {cap.get('chromium_browser')}",
            ]
            return "\n".join(lines), extra

        login_notice = action_type == "browser_login_required_notice"
        session = self.prepare_approved_launch(
            target=target,
            action_id=action_id or "",
            chat_session_id=chat_session_id,
            login_notice=login_notice,
        )
        self.enqueue_launch(session.id)
        extra["browser_session_id"] = session.id
        extra["browser_session_status"] = BrowserSessionStatus.LAUNCHING.value
        return (
            f"Supervised browser session queued for `{target}`.\n"
            "Launch runs in the background — lifecycle updates appear in chat and Mission Control.",
            extra,
        )

    # Backward-compatible alias for tests
    def start_supervised_session(
        self,
        *,
        target: str,
        action_id: str | None = None,
        chat_session_id: str = "default",
        login_notice: bool = False,
    ) -> BrowserSession:
        session = self.prepare_approved_launch(
            target=target,
            action_id=action_id or "",
            chat_session_id=chat_session_id,
            login_notice=login_notice,
        )
        self.launch_session_worker(session.id)
        with self._lock:
            return self._sessions[session.id]


browser_session_store = BrowserSessionStore()

# SPDX-License-Identifier: Apache-2.0
"""Browser executor observability and safe recovery."""

from __future__ import annotations

import logging
import threading
import time
from collections.abc import Callable
from dataclasses import dataclass
from typing import Any, TypeVar

T = TypeVar("T")

_log = logging.getLogger(__name__)


@dataclass
class _SyncJob:
    fn: Callable[[], Any]
    reply: Any


@dataclass
class BrowserExecutorStatus:
    running: bool
    thread_id: int | None
    queue_depth: int
    launch_queue_depth: int
    active_operation: str | None
    last_error: str | None
    last_error_at: float | None
    last_success_at: float | None

    def to_dict(self) -> dict[str, Any]:
        return {
            "running": self.running,
            "thread_id": self.thread_id,
            "queue_depth": self.queue_depth,
            "launch_queue_depth": self.launch_queue_depth,
            "active_operation": self.active_operation,
            "last_error": self.last_error,
            "last_error_at": self.last_error_at,
            "last_success_at": self.last_success_at,
        }


class BrowserExecutor:
    def __init__(self) -> None:
        self._launch_queue: Any = None
        self._sync_queue: Any = None
        self._thread: threading.Thread | None = None
        self._thread_id: int | None = None
        self._stop = threading.Event()
        self._active_operation: str | None = None
        self._last_error: str | None = None
        self._last_error_at: float | None = None
        self._last_success_at: float | None = None
        self._init_queues()

    def _init_queues(self) -> None:
        import queue

        self._launch_queue = queue.Queue()
        self._sync_queue = queue.Queue()

    def thread_id(self) -> int | None:
        return self._thread_id

    def is_browser_thread(self) -> bool:
        tid = self._thread_id
        return tid is not None and threading.get_ident() == tid

    def set_active_operation(self, name: str | None) -> None:
        self._active_operation = name

    def record_success(self) -> None:
        self._last_success_at = time.time()
        self._active_operation = None

    def record_error(self, message: str, *, operation: str | None = None) -> None:
        self._last_error = message[:500]
        self._last_error_at = time.time()
        self._active_operation = None
        _log.error(
            "browser_executor_error operation=%s thread_id=%s error=%s",
            operation or "unknown",
            self._thread_id,
            message,
        )

    def status(self) -> BrowserExecutorStatus:
        return BrowserExecutorStatus(
            running=bool(self._thread and self._thread.is_alive()),
            thread_id=self._thread_id,
            queue_depth=self._sync_queue.qsize(),
            launch_queue_depth=self._launch_queue.qsize(),
            active_operation=self._active_operation,
            last_error=self._last_error,
            last_error_at=self._last_error_at,
            last_success_at=self._last_success_at,
        )

    def start(self) -> None:
        if self._thread and self._thread.is_alive():
            return
        self._stop.clear()
        self._thread = threading.Thread(
            target=self._loop,
            name="aethos-browser-executor",
            daemon=True,
        )
        self._thread.start()

    def stop(self) -> None:
        self._stop.set()
        if self._thread:
            self._thread.join(timeout=2.0)
            self._thread = None
            self._thread_id = None

    def reset(self) -> None:
        """Restart executor thread after runtime failure — saved profiles untouched."""
        _log.warning("browser_executor_reset")
        self.stop()
        self._init_queues()
        self._active_operation = None
        self.start()

    def enqueue(self, session_id: str) -> None:
        self._launch_queue.put(session_id)

    def run_sync(self, fn: Callable[[], T], *, timeout: float = 90.0) -> T:
        if self.is_browser_thread():
            return fn()
        self.start()
        import queue

        job = _SyncJob(fn=fn, reply=queue.Queue(maxsize=1))
        self._sync_queue.put(job)
        try:
            outcome = job.reply.get(timeout=timeout)
        except queue.Empty as exc:
            self.record_error("Browser operation timed out", operation=self._active_operation)
            raise TimeoutError("Browser operation timed out") from exc
        if isinstance(outcome, BaseException):
            raise outcome
        return outcome

    def drain_once_for_tests(self) -> bool:
        try:
            session_id = self._launch_queue.get_nowait()
        except Exception:
            return False
        from aethos_core.runtime.browser_session import browser_session_store

        self.run_sync(lambda: browser_session_store.launch_session_worker(session_id))
        self._launch_queue.task_done()
        return True

    def drain_sync_for_tests(self) -> bool:
        try:
            job = self._sync_queue.get_nowait()
        except Exception:
            return False
        try:
            job.reply.put(job.fn())
        except BaseException as exc:
            job.reply.put(exc)
        return True

    def drain_queue_for_tests(self) -> None:
        self.stop()
        while True:
            try:
                self._launch_queue.get_nowait()
                self._launch_queue.task_done()
            except Exception:
                break
        while True:
            try:
                self._sync_queue.get_nowait()
            except Exception:
                break

    def _loop(self) -> None:
        from aethos_core.runtime.browser_session import browser_session_store

        self._thread_id = threading.get_ident()
        while not self._stop.is_set():
            try:
                job = self._sync_queue.get(timeout=0.05)
            except Exception:
                job = None
            if job is not None:
                try:
                    job.reply.put(job.fn())
                except BaseException as exc:
                    job.reply.put(exc)
                continue

            try:
                session_id = self._launch_queue.get(timeout=0.35)
            except Exception:
                continue
            try:
                browser_session_store.launch_session_worker(session_id)
            finally:
                self._launch_queue.task_done()


browser_executor = BrowserExecutor()


def get_browser_executor_status() -> dict[str, Any]:
    return browser_executor.status().to_dict()


def reset_browser_executor() -> dict[str, Any]:
    browser_executor.reset()
    return get_browser_executor_status()

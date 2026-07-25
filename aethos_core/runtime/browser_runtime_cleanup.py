# SPDX-License-Identifier: Apache-2.0
"""Browser heartbeat loop and orphan session cleanup."""

from __future__ import annotations

import threading
from time import time

from aethos_core.config import get_settings


class BrowserRuntimeCleanup:
    def __init__(self) -> None:
        self._thread: threading.Thread | None = None
        self._stop = threading.Event()

    def start(self) -> None:
        if self._thread and self._thread.is_alive():
            return
        self._stop.clear()
        self._thread = threading.Thread(
            target=self._loop,
            name="aethos-browser-cleanup",
            daemon=True,
        )
        self._thread.start()

    def stop(self) -> None:
        self._stop.set()
        if self._thread:
            self._thread.join(timeout=2.0)
            self._thread = None

    def run_once(self) -> None:
        from aethos_core.runtime.browser_session import browser_session_store

        get_settings()
        browser_session_store.tick_heartbeats()
        browser_session_store.cleanup_stale_sessions()

    def cleanup_all(self) -> None:
        from aethos_core.runtime.browser_session import browser_session_store

        browser_session_store.close_all()

    def _loop(self) -> None:
        while not self._stop.is_set():
            try:
                self.run_once()
            except Exception:
                pass
            s = get_settings()
            self._stop.wait(timeout=max(1.0, s.browser_heartbeat_interval_sec))


browser_runtime_cleanup = BrowserRuntimeCleanup()

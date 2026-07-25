# SPDX-License-Identifier: Apache-2.0
"""Background dispatcher loop for autonomous execution plane."""

from __future__ import annotations

import logging
import threading
import time

_log = logging.getLogger(__name__)
_STOP = threading.Event()
_THREAD: threading.Thread | None = None


def start_autonomous_dispatcher_loop() -> None:
    global _THREAD
    from aethos_core.config import get_settings

    if not getattr(get_settings(), "autonomous_execution_plane_enabled", False):
        return
    if _THREAD and _THREAD.is_alive():
        return
    _STOP.clear()

    def _run() -> None:
        from aethos_core.autonomous_execution.plane_service import dispatch_until_idle

        while not _STOP.is_set():
            try:
                dispatch_until_idle(max_ticks=4)
            except Exception:
                _log.exception("autonomous_dispatcher_tick_failed")
            _STOP.wait(2.0)

    _THREAD = threading.Thread(target=_run, name="aethos-autonomous-dispatcher", daemon=True)
    _THREAD.start()


def stop_autonomous_dispatcher_loop() -> None:
    _STOP.set()

# SPDX-License-Identifier: Apache-2.0
"""Standalone worker entrypoint — isolated from API process."""

from __future__ import annotations

import logging
import signal
import sys
import time

_log = logging.getLogger("aethos.worker")


def run_worker(*, worker_id: str | None = None) -> None:
    """Start worker process — job executor + observation scheduler only."""
    from uuid import uuid4

    from aethos_core.config import get_settings
    from aethos_core.runtime.browser_executor import browser_executor
    from aethos_core.runtime.job_executor import job_executor
    from aethos_core.runtime.schedulers.observation_scheduler import start_observation_scheduler, stop_observation_scheduler

    wid = worker_id or f"worker-{uuid4().hex[:8]}"
    s = get_settings()
    _log.info("AethOS worker starting id=%s mode=%s", wid, getattr(s, "worker_mode", "standalone"))

    from aethos_core.canvas.canvas_store import init_canvas_store_schema

    init_canvas_store_schema()

    job_executor.start()
    browser_executor.start()
    start_observation_scheduler()

    stop = False

    def _handle_sigterm(*_args) -> None:
        nonlocal stop
        stop = True

    signal.signal(signal.SIGTERM, _handle_sigterm)
    signal.signal(signal.SIGINT, _handle_sigterm)

    try:
        while not stop:
            time.sleep(2.0)
    finally:
        stop_observation_scheduler()
        browser_executor.stop()
        job_executor.stop()
        _log.info("AethOS worker stopped id=%s", wid)


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="[AethOS worker] %(message)s")
    run_worker()
    sys.exit(0)


if __name__ == "__main__":
    main()

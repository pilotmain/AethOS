# SPDX-License-Identifier: Apache-2.0

import threading

from aethos_core.runtime.browser_executor import browser_executor


def test_run_sync_executes_on_browser_thread():
    observed: list[str] = []

    def work() -> str:
        observed.append(threading.current_thread().name)
        return "ok"

    result = browser_executor.run_sync(work, timeout=5.0)
    assert result == "ok"
    assert observed
    assert observed[0] == "aethos-browser-executor"

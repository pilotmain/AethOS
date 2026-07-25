# SPDX-License-Identifier: Apache-2.0

from aethos_core.runtime.browser_executor import browser_executor, reset_browser_executor
from aethos_core.runtime.browser_runtime import BrowserRuntimeBoundaryError, run_browser_sync


def test_browser_executor_recovers_after_boundary_failure():
    browser_executor.drain_queue_for_tests()
    calls = {"n": 0}

    def failing() -> None:
        calls["n"] += 1
        raise BrowserRuntimeBoundaryError("test boundary")

    try:
        run_browser_sync(failing, operation="test_fail")
        assert False, "expected failure"
    except BrowserRuntimeBoundaryError:
        pass

    assert browser_executor.status().last_error is not None

    def ok() -> str:
        return "ok"

    assert run_browser_sync(ok, operation="test_ok") == "ok"
    assert browser_executor.status().last_success_at is not None
    browser_executor.drain_queue_for_tests()

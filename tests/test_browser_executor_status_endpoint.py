# SPDX-License-Identifier: Apache-2.0

from aethos_core.runtime.browser_executor import browser_executor, get_browser_executor_status, reset_browser_executor


def test_browser_executor_status_endpoint_shape():
    from aethos_core.api.main import app
    from fastapi.testclient import TestClient

    browser_executor.drain_queue_for_tests()
    client = TestClient(app)
    r = client.get("/api/v1/browser/executor/status")
    assert r.status_code == 200
    data = r.json()
    assert "running" in data
    assert "thread_id" in data
    assert "queue_depth" in data
    assert "active_operation" in data
    assert "last_error" in data
    assert "last_success_at" in data


def test_get_browser_executor_status_helper():
    browser_executor.drain_queue_for_tests()
    status = get_browser_executor_status()
    assert isinstance(status["running"], bool)
    assert status["queue_depth"] == 0


def test_reset_browser_executor_restarts_thread():
    browser_executor.drain_queue_for_tests()
    browser_executor.start()
    seen: list[int | None] = []

    def work() -> None:
        seen.append(browser_executor.thread_id())

    browser_executor.run_sync(work, timeout=5.0)
    reset_browser_executor()
    seen.clear()
    browser_executor.run_sync(work, timeout=5.0)
    assert seen[0] is not None
    browser_executor.drain_queue_for_tests()

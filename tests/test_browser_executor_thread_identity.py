# SPDX-License-Identifier: Apache-2.0

from aethos_core.runtime.browser_executor import browser_executor


def test_browser_executor_thread_identity():
    browser_executor.start()
    try:
        seen: list[int | None] = []

        def work() -> None:
            seen.append(browser_executor.thread_id())

        browser_executor.run_sync(work, timeout=5.0)
        assert seen[0] is not None
        assert browser_executor.thread_id() == seen[0]
    finally:
        browser_executor.drain_queue_for_tests()

# SPDX-License-Identifier: Apache-2.0

from aethos_core.runtime.browser_diagnostics import (
    clear_browser_diagnostics_cache_for_tests,
    last_successful_browser_use_at,
    probe_playwright_on_browser_thread,
    record_browser_operation_success,
    set_playwright_runtime_override,
)


def test_success_clears_stale_failure():
    set_playwright_runtime_override(None)
    clear_browser_diagnostics_cache_for_tests()
    record_browser_operation_success()
    assert last_successful_browser_use_at() is not None
    diag = probe_playwright_on_browser_thread()
    assert diag["execution_ready"] is True
    assert diag["launch_probe_ok"] is True
    clear_browser_diagnostics_cache_for_tests()

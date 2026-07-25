# SPDX-License-Identifier: Apache-2.0

import inspect

from aethos_core.runtime import browser_diagnostics as bd


def test_launch_probe_runs_via_browser_executor():
    src = inspect.getsource(bd.probe_playwright_on_browser_thread)
    assert "run_browser_sync" in src


def test_import_only_probe_avoids_sync_playwright():
    diag = bd._probe_import_only()
    assert diag.get("launch_probe_ok") is False
    assert diag.get("launch_probe_error") is None

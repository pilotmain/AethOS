# SPDX-License-Identifier: Apache-2.0

import inspect

from aethos_core.runtime.browser_capability import get_browser_runtime_diagnostics


def test_browser_diagnostics_uses_browser_thread_probe():
    src = inspect.getsource(get_browser_runtime_diagnostics)
    assert "probe_playwright_on_browser_thread" in src

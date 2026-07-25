# SPDX-License-Identifier: Apache-2.0

import inspect

from aethos_core.operations.execution import execution_runner as er


def test_readonly_execution_browser_path_uses_browser_runtime():
    src = inspect.getsource(er._try_browser_log_excerpt)
    assert "run_playwright_on_browser_thread" in src

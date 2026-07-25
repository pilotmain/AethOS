# SPDX-License-Identifier: Apache-2.0

import inspect

from aethos_core.runtime import vercel_readonly_inspector as insp


def test_vercel_inventory_uses_run_browser_sync():
    src = inspect.getsource(insp.run_readonly_inspection)
    assert "run_browser_sync" in src

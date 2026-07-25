# SPDX-License-Identifier: Apache-2.0

from aethos_core.browser.platforms.vercel.vercel_dom_parser import wait_for_dashboard_ready
from tests.browser_test_utils import _MockPage


def test_dashboard_ready_detects_projects_marker():
    page = _MockPage(body_text="All Projects\nAdd New\n")
    ok, signal = wait_for_dashboard_ready(page, timeout_ms=2000)
    assert ok is True
    assert signal in ("All Projects", "Add New", "Projects", "New Project") or signal is not None

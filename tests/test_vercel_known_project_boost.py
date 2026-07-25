# SPDX-License-Identifier: Apache-2.0

from aethos_core.browser.platforms.vercel.vercel_dom_parser import parse_projects_from_page
from tests.browser_test_utils import _MockPage


def test_memory_confirmed_survives_thin_dom_signal():
    page = _MockPage(
        project_hrefs=[("https://vercel.com/acme/invoicepilot", "invoicepilot")],
        body_text="Projects\n",
    )
    parsed = parse_projects_from_page(page, known_projects=["invoicepilot"])
    names = [p.name for p in parsed.projects]
    assert "invoicepilot" in names
    assert parsed.pipeline.known_memory_matches >= 1

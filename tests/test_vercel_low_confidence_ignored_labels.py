# SPDX-License-Identifier: Apache-2.0

from aethos_core.browser.platforms.vercel.vercel_dom_parser import parse_projects_from_page
from tests.browser_test_utils import _MockPage


def test_low_confidence_nav_labels_in_ignored():
    page = _MockPage(
        project_hrefs=[
            ("https://vercel.com/acme/invoicepilot", "invoicepilot"),
            ("https://vercel.com/acme/quotepilot", "quotepilot"),
            ("https://vercel.com/acme/cdn", "cdn"),
        ],
        body_text="Projects\n",
    )
    result = parse_projects_from_page(page)
    names = [p.name for p in result.projects]
    assert "invoicepilot" in names
    assert "quotepilot" in names
    assert "cdn" not in names

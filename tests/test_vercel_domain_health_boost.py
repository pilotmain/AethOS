# SPDX-License-Identifier: Apache-2.0

from aethos_core.browser.platforms.vercel.vercel_dom_parser import parse_projects_from_page
from tests.browser_test_utils import _MockPage


def test_domain_in_card_prevents_false_degraded():
    page = _MockPage(
        project_hrefs=[
            (
                "https://vercel.com/acme/invoicepilot",
                "invoicepilot\nuseinvoicepilot.com\nProduction",
            ),
        ],
        body_text="Projects\n",
    )
    parsed = parse_projects_from_page(page)
    inv = next(p for p in parsed.projects if p.name == "invoicepilot")
    assert inv.production_url
    assert "useinvoicepilot" in inv.production_url or "invoicepilot" in inv.production_url

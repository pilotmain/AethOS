# SPDX-License-Identifier: Apache-2.0

from aethos_core.browser.platforms.vercel.vercel_dom_parser import parse_projects_from_page
from tests.browser_test_utils import _MockPage


def test_pipeline_counts_reported():
    page = _MockPage(
        project_hrefs=[
            ("https://vercel.com/acme/invoicepilot", "invoicepilot"),
            ("https://vercel.com/acme/quotepilot", "quotepilot"),
        ],
        body_text="All Projects\nAdd New\n",
    )
    parsed = parse_projects_from_page(page)
    p = parsed.pipeline
    assert p.raw_links_seen >= 2
    assert p.project_like_links_seen >= 2
    assert p.candidate_names_seen >= 2
    assert p.candidates_after_confidence >= 2
    assert len(parsed.projects) >= 2

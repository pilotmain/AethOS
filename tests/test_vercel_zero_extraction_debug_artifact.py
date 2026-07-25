# SPDX-License-Identifier: Apache-2.0

from aethos_core.browser.platforms.vercel.vercel_dom_parser import (
    build_extraction_debug,
    parse_projects_from_page,
)
from tests.browser_test_utils import _MockPage


def test_zero_extraction_includes_debug_artifact():
    page = _MockPage(project_hrefs=[], body_text="Loading…\n")
    parsed = parse_projects_from_page(page, known_projects=[])
    debug = build_extraction_debug(
        page_url="https://vercel.com/dashboard",
        page_title="Vercel",
        parsed=parsed,
        visible_text_excerpt="Loading",
        known_memory_projects=[],
    )
    assert parsed.projects == []
    assert debug["raw_link_count"] >= 0
    assert "pipeline" in debug
    assert "visible_text_excerpt" in debug
    assert debug["candidate_count"] == 0 or debug["pipeline"]["candidate_names_seen"] == 0

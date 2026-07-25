# SPDX-License-Identifier: Apache-2.0

from aethos_core.browser.platforms.vercel.vercel_production_urls import (
    _domain_matches_project,
    best_production_url,
)


def test_useinvoicepilot_matches_invoicepilot_not_wingman():
    assert _domain_matches_project("useinvoicepilot.com", "invoicepilot")
    assert not _domain_matches_project("useinvoicepilot.com", "wingman")
    assert not _domain_matches_project("useinvoicepilot.com", "pilotos-site")


def test_card_scoped_url_extraction():
    url, source, conf = best_production_url(
        project_name="quotepilot",
        card_text="quotepilot\nquotepilotnow.com\nProduction",
    )
    assert url
    assert "quotepilot" in url
    assert conf in ("high", "medium")

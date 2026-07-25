# SPDX-License-Identifier: Apache-2.0

from aethos_core.browser.platforms.vercel.vercel_production_urls import (
    best_production_url,
    extract_urls_from_text,
)


def test_custom_domain_extracted():
    matches = extract_urls_from_text(
        "invoicepilot\nProduction\nuseinvoicepilot.com",
        "invoicepilot",
    )
    assert matches
    assert any("useinvoicepilot.com" in m.url for m in matches)


def test_vercel_app_subdomain():
    url, source, _conf = best_production_url(
        project_name="quotepilot",
        card_text="quotepilot\nquotepilotnow.com\nReady",
    )
    assert url
    assert "quotepilot" in url or "quotepilotnow" in url
    assert source in ("custom_domain", "anchor_url", "production_badge", "vercel_app_text")

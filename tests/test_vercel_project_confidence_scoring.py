# SPDX-License-Identifier: Apache-2.0

from aethos_core.browser.platforms.vercel.vercel_project_scoring import (
    CONFIRMED_THRESHOLD,
    bucket_candidates,
    score_candidate,
)


def test_real_project_link_scores_confirmed():
    c = score_candidate(
        "invoicepilot",
        href="https://vercel.com/acme/invoicepilot",
        from_dom=True,
        card_text="invoicepilot\ninvoicepilot.vercel.app\nReady github.com/acme/invoicepilot",
    )
    assert c is not None
    buckets = bucket_candidates({c.name: c})
    assert buckets.confirmed
    assert c.score >= CONFIRMED_THRESHOLD


def test_bare_product_slug_rejected():
    c = score_candidate("cdn", from_text_fallback=True)
    assert c is None

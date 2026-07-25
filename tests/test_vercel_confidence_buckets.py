# SPDX-License-Identifier: Apache-2.0

from aethos_core.browser.platforms.vercel.vercel_project_scoring import (
    CONFIRMED_THRESHOLD,
    LIKELY_THRESHOLD,
    bucket_candidates,
    score_candidate,
)


def test_confirmed_requires_higher_score():
    rich = score_candidate(
        "invoicepilot",
        href="https://vercel.com/acme/invoicepilot",
        from_dom=True,
        card_text="invoicepilot.vercel.app Ready github.com/acme/invoicepilot",
    )
    assert rich is not None
    buckets = bucket_candidates({rich.name: rich})
    assert buckets.confirmed
    assert rich.score >= CONFIRMED_THRESHOLD


def test_thin_dom_link_is_likely_not_confirmed():
    thin = score_candidate(
        "lifeos",
        href="https://example.com/lifeos",
        from_dom=True,
    )
    assert thin is not None
    buckets = bucket_candidates({thin.name: thin})
    assert not buckets.confirmed
    assert buckets.likely
    assert thin.score >= LIKELY_THRESHOLD
    assert thin.score < CONFIRMED_THRESHOLD

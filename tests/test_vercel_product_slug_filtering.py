# SPDX-License-Identifier: Apache-2.0

from aethos_core.browser.platforms.vercel.vercel_navigation_map import (
    is_platform_feature_slug,
    is_usage_metric_slug,
)
from aethos_core.runtime.vercel_inventory import extract_projects_from_page
from tests.browser_test_utils import _MockPage


def test_known_product_slugs_filtered():
    assert is_platform_feature_slug("cdn")
    assert is_platform_feature_slug("stores")
    assert is_usage_metric_slug("vercel-functions-invocations")


def test_extraction_ignores_product_hrefs():
    page = _MockPage(
        project_hrefs=[
            ("https://vercel.com/acme/invoicepilot", "invoicepilot"),
            ("https://vercel.com/raya-team/cdn", "cdn"),
            ("https://vercel.com/raya-team/vercel-functions-invocations", "vercel-functions-invocations"),
        ],
    )
    projects, _ = extract_projects_from_page(page)
    names = [p.name for p in projects]
    assert "invoicepilot" in names
    assert "cdn" not in names
    assert "vercel-functions-invocations" not in names

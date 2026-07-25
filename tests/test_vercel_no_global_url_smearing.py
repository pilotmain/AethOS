# SPDX-License-Identifier: Apache-2.0

from aethos_core.browser.platforms.vercel.vercel_entities import VercelProject
from aethos_core.browser.platforms.vercel.vercel_production_urls import dedupe_shared_production_urls


def test_shared_url_cleared_from_unrelated_projects():
    projects = [
        VercelProject(
            name="invoicepilot",
            production_url="https://useinvoicepilot.com",
            production_url_source="custom_domain",
            production_url_confidence="high",
        ),
        VercelProject(
            name="wingman",
            production_url="https://useinvoicepilot.com",
            production_url_source="custom_domain",
            production_url_confidence="high",
        ),
        VercelProject(
            name="pilotos-site",
            production_url="https://useinvoicepilot.com",
            production_url_source="custom_domain",
            production_url_confidence="high",
        ),
    ]
    dedupe_shared_production_urls(projects)
    with_url = [p for p in projects if p.production_url]
    assert len(with_url) == 1
    assert with_url[0].name == "invoicepilot"

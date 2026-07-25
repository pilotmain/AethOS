# SPDX-License-Identifier: Apache-2.0

from aethos_core.runtime.vercel_inventory import extract_projects_from_page
from tests.browser_test_utils import _MockPage


def test_dom_extraction_from_project_links():
    page = _MockPage(
        project_hrefs=[
            ("https://vercel.com/acme/invoicepilot", "invoicepilot"),
            ("https://vercel.com/acme/lifeos", "lifeos"),
            ("https://vercel.com/acme/pilot-os-ui", "pilot-os-ui"),
        ],
        body_text="Projects\n",
    )
    projects, method = extract_projects_from_page(page)
    names = [p.name for p in projects]
    assert method in ("dom", "dom_semantic")
    assert "invoicepilot" in names
    assert "lifeos" in names
    assert "pilot-os-ui" in names
    assert "analytics" not in names
    assert "deployments" not in names
    assert "hobby" not in names


def test_text_fallback_filters_nav_labels():
    page = _MockPage(
        project_hrefs=[
            ("https://vercel.com/acme/invoicepilot", "invoicepilot"),
            ("https://vercel.com/acme/quotepilot", "quotepilot"),
        ],
        body_text="Projects\nHobby\nDeployments\nAnalytics\n",
    )
    projects, method = extract_projects_from_page(page)
    names = [p.name for p in projects]
    assert "invoicepilot" in names
    assert "quotepilot" in names
    assert "hobby" not in names
    assert "deployments" not in names
    assert "analytics" not in names

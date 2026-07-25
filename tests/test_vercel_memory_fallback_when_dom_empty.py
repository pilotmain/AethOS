# SPDX-License-Identifier: Apache-2.0

from aethos_core.browser.platforms.vercel.vercel_inventory_builder import (
    build_inventory_from_page,
    build_operational_summary,
)
from tests.browser_test_utils import _MockPage


def test_memory_fallback_when_dom_empty():
    page = _MockPage(project_hrefs=[], body_text="Projects\n")
    artifact, method = build_inventory_from_page(
        page,
        known_projects=["invoicepilot", "quotepilot", "pilot-os-ui"],
    )
    assert method == "operational_memory_fallback"
    assert artifact.memory_fallback is True
    names = [p.name for p in artifact.projects]
    assert "invoicepilot" in names
    assert "quotepilot" in names
    summary = build_operational_summary(artifact)
    assert "memory" in summary.lower()
    assert "invoicepilot" in summary
    assert "Found 0 Vercel projects" not in summary

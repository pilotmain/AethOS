# SPDX-License-Identifier: Apache-2.0

from aethos_core.browser.platforms.vercel.vercel_entities import HealthState, VercelProject
from aethos_core.browser.platforms.vercel.vercel_health_classifier import classify_project_health


def test_detail_verified_url_upgrades_to_healthy():
    p = VercelProject(
        name="quotepilot",
        production_url="https://quotepilotnow.com",
        production_url_source="detail_page",
        production_url_confidence="high",
        production_url_verified=True,
    )
    assert classify_project_health(p) == HealthState.HEALTHY

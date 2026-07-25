# SPDX-License-Identifier: Apache-2.0

from aethos_core.browser.platforms.vercel.vercel_entities import HealthState, VercelProject
from aethos_core.browser.platforms.vercel.vercel_health_classifier import (
    classify_project_health,
    operator_display_label,
)


def test_failed_preview_with_healthy_production_url():
    p = VercelProject(
        name="pilot-os-ui",
        production_url="https://pilot-os-ui.vercel.app",
        production_url_source="detail_page",
        production_url_confidence="high",
        production_url_verified=True,
        deployment_state="failed",
        deployment_status="preview deployment failed",
    )
    health = classify_project_health(p)
    assert health in (HealthState.LIKELY_DEGRADED, HealthState.UNKNOWN)
    assert p.production_health == "healthy"
    label = operator_display_label(p).lower()
    assert "production healthy" in label or "preview" in label or "needs attention" in label
    assert p.production_health == "healthy"

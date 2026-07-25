# SPDX-License-Identifier: Apache-2.0

from aethos_core.browser.platforms.vercel.vercel_entities import HealthState, VercelProject
from aethos_core.browser.platforms.vercel.vercel_health_classifier import (
    apply_health_to_projects,
    display_attention_label,
)


def test_unknown_not_marked_degraded():
    projects = [
        VercelProject(name="lifeos"),
        VercelProject(name="wingman"),
    ]
    summary = apply_health_to_projects(projects)
    assert "lifeos" in summary.unknown
    assert "wingman" in summary.unknown
    assert "lifeos" not in summary.degraded
    assert display_attention_label(projects[0]) == "production status not confirmed"


def test_failed_stays_failed():
    p = VercelProject(
        name="broken",
        production_url="https://broken.vercel.app",
        production_url_source="detail_page",
        production_url_confidence="high",
        production_url_verified=True,
        deployment_state="failed",
        deployment_status="production deployment failed",
    )
    summary = apply_health_to_projects([p])
    assert p.health == HealthState.FAILED
    assert "broken" in summary.failed

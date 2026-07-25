# SPDX-License-Identifier: Apache-2.0

from aethos_core.browser.platforms.vercel.vercel_entities import HealthState, VercelProject
from aethos_core.browser.platforms.vercel.vercel_health_classifier import (
    classify_project_health,
    infer_production_health,
)


def test_preview_url_with_failed_deploy_not_production_down():
    p = VercelProject(
        name="invoicepilot",
        production_url="https://invoicepilot-nnusvd68a-rayameresas-projects.vercel.app",
        deployment_state="failed",
    )
    classify_project_health(p)
    assert p.url_type == "preview_vercel"
    assert p.production_health != "down"
    assert p.health != HealthState.FAILED


def test_custom_domain_with_production_ready_is_healthy():
    p = VercelProject(
        name="invoicepilot",
        production_url="https://useinvoicepilot.com",
        production_url_source="custom_domain",
        production_url_confidence="high",
        production_url_verified=True,
        deployment_state="ready",
    )
    assert classify_project_health(p) == HealthState.HEALTHY
    assert infer_production_health(p) == "healthy"

# SPDX-License-Identifier: Apache-2.0

from aethos_core.browser.platforms.vercel.vercel_entities import HealthState, VercelProject
from aethos_core.browser.platforms.vercel.vercel_health_classifier import classify_project_health


def test_custom_domain_is_healthy():
    p = VercelProject(
        name="invoicepilot",
        production_url="https://useinvoicepilot.com",
        production_url_source="detail_page",
        production_url_confidence="high",
        production_url_verified=True,
    )
    assert classify_project_health(p) == HealthState.HEALTHY


def test_deploy_activity_without_url_is_likely_healthy():
    p = VercelProject(
        name="pilot-os-ui",
        git_repo="github.com/acme/pilot-os-ui",
        deployment_state="deployed",
    )
    assert classify_project_health(p) == HealthState.LIKELY_HEALTHY


def test_no_evidence_is_unknown():
    p = VercelProject(name="lifeos")
    assert classify_project_health(p) == HealthState.UNKNOWN

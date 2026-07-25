# SPDX-License-Identifier: Apache-2.0

from aethos_core.browser.platforms.vercel.vercel_entities import HealthState, VercelProject
from aethos_core.browser.platforms.vercel.vercel_health_classifier import classify_project_health


def test_no_url_no_explicit_failure_is_unknown():
    p = VercelProject(name="lifeos")
    assert classify_project_health(p) == HealthState.UNKNOWN


def test_verified_url_is_healthy():
    p = VercelProject(
        name="invoicepilot",
        production_url="https://useinvoicepilot.com",
        production_url_source="detail_page",
        production_url_confidence="high",
        production_url_verified=True,
    )
    assert classify_project_health(p) == HealthState.HEALTHY


def test_unverified_medium_url_is_likely_healthy():
    p = VercelProject(
        name="pilot-os-ui",
        production_url="https://pilot-os-ui.vercel.app",
        production_url_source="vercel_app_text",
        production_url_confidence="medium",
        deployment_state="deployed",
        git_repo="github.com/acme/pilot-os-ui",
    )
    assert classify_project_health(p) in (HealthState.LIKELY_HEALTHY, HealthState.HEALTHY)

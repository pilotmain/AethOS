# SPDX-License-Identifier: Apache-2.0

from aethos_core.browser.platforms.vercel.vercel_entities import VercelProject
from aethos_core.browser.platforms.vercel.vercel_health_classifier import (
    apply_deployment_semantics,
    collect_health_evidence,
    operator_display_label,
)


def test_evidence_includes_production_scope_when_detected():
    p = VercelProject(
        name="invoicepilot",
        production_url="https://useinvoicepilot.com",
        production_url_source="custom_domain",
        production_url_verified=True,
        deployment_state="failed",
        last_deploy_state="failed",
    )
    apply_deployment_semantics(p)
    evidence = collect_health_evidence(p)
    assert "latest_deployment_failed" in evidence
    if p.latest_deployment_scope == "production":
        assert "scope_detected: production" in evidence


def test_production_down_requires_production_scope():
    p = VercelProject(
        name="invoicepilot",
        production_url="https://invoicepilot-a1b2c3d4.vercel.app",
        deployment_state="failed",
        last_deploy_state="failed",
    )
    apply_deployment_semantics(p)
    label = operator_display_label(p)
    assert "production down" not in label.lower()
    assert "unclear" in label.lower() or "failed" in label.lower()

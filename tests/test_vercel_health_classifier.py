# SPDX-License-Identifier: Apache-2.0

from aethos_core.browser.platforms.vercel.vercel_entities import HealthState, VercelProject
from aethos_core.browser.platforms.vercel.vercel_health_classifier import (
    apply_health_to_projects,
    attention_reason_for,
    classify_project_health,
    enrich_inventory,
)
from aethos_core.browser.platforms.vercel.vercel_inventory_builder import build_inventory_artifact


def test_failed_production_deployment_classified():
    p = VercelProject(
        name="broken-app",
        production_url="https://broken-app.vercel.app",
        production_url_source="detail_page",
        production_url_confidence="high",
        production_url_verified=True,
        deployment_state="failed",
        deployment_status="production deployment failed",
    )
    assert classify_project_health(p) == HealthState.FAILED
    assert "failed" in (attention_reason_for(p) or "").lower()


def test_failed_without_production_url_is_needs_attention_not_blind_failed():
    p = VercelProject(name="broken-app", deployment_state="failed")
    assert classify_project_health(p) == HealthState.LIKELY_DEGRADED


def test_preview_without_url_is_unknown_not_degraded():
    p = VercelProject(name="lifeos", deployment_state="preview")
    assert classify_project_health(p) == HealthState.UNKNOWN
    assert p.attention_reason in (None, "preview only")


def test_explicit_no_production_is_likely_degraded():
    p = VercelProject(
        name="lifeos",
        deployment_state="no_production",
        deployment_status="no production deployment",
    )
    assert classify_project_health(p) == HealthState.LIKELY_DEGRADED


def test_healthy_with_verified_production_url():
    p = VercelProject(
        name="invoicepilot",
        production_url="https://invoicepilot.vercel.app",
        production_url_source="detail_page",
        production_url_confidence="high",
        production_url_verified=True,
        deployment_state="ready",
    )
    assert classify_project_health(p) == HealthState.HEALTHY


def test_inventory_enrichment_counts():
    artifact = build_inventory_artifact(
        [
            VercelProject(
                name="ok",
                production_url="https://ok.vercel.app",
                production_url_source="detail_page",
                production_url_confidence="high",
                production_url_verified=True,
                deployment_state="ready",
            ),
            VercelProject(
                name="bad",
                production_url="https://bad.vercel.app",
                production_url_source="detail_page",
                production_url_confidence="high",
                production_url_verified=True,
                deployment_state="failed",
                deployment_status="production failed",
            ),
        ],
        extraction_method="test",
    )
    enrich_inventory(artifact)
    assert artifact.healthy_count >= 1
    assert artifact.failing_count >= 1
    assert len(artifact.health_summary.needs_attention) >= 1

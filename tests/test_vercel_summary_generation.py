# SPDX-License-Identifier: Apache-2.0

from aethos_core.runtime.vercel_inventory import (
    VercelProject,
    build_chat_summary_bullets,
    build_inventory_artifact,
    build_operational_summary,
)


def test_operational_summary_lists_real_projects_not_nav():
    artifact = build_inventory_artifact(
        [
            VercelProject(
                name="invoicepilot",
                production_url="https://useinvoicepilot.com",
                deployment_state="ready",
            ),
            VercelProject(
                name="quotepilot",
                production_url="https://quotepilotnow.com",
                deployment_state="ready",
            ),
            VercelProject(name="lifeos", deployment_state="failed"),
        ],
        extraction_method="dom",
    )
    summary = build_operational_summary(artifact)
    assert "invoicepilot" in summary
    assert "quotepilot" in summary
    assert "lifeos" in summary
    assert "Healthy:" in summary or "Likely healthy:" in summary
    assert "Needs attention:" in summary
    assert "latest deployment failed" in summary.lower() or "needs attention" in summary.lower()
    assert "Analytics" not in summary
    assert "Deployments" not in summary
    assert "**3**" in summary or "3 Vercel project" in summary
    assert "Mission Control" in summary


def test_chat_bullets_are_concise():
    artifact = build_inventory_artifact(
        [VercelProject(name="my-app")],
        extraction_method="dom",
    )
    bullets = build_chat_summary_bullets(artifact)
    assert "confirmed Vercel project" in bullets
    assert "my-app" in bullets
    assert len(bullets) < 500

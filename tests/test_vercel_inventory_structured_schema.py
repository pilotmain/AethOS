# SPDX-License-Identifier: Apache-2.0

from aethos_core.runtime.vercel_inventory import (
    VercelInventoryArtifact,
    VercelProject,
    build_inventory_artifact,
)


def test_inventory_artifact_schema():
    projects = [
        VercelProject(
            name="invoicepilot",
            deployment_state="ready",
            production_url="https://invoicepilot.vercel.app",
            production_url_source="detail_page",
            production_url_confidence="high",
            production_url_verified=True,
        ),
        VercelProject(name="lifeos", deployment_state="failed"),
    ]
    artifact = build_inventory_artifact(projects, extraction_method="dom")
    data = artifact.to_dict()
    assert data["project_count"] == 2
    assert len(data["projects"]) == 2
    assert data["projects"][0]["name"] == "invoicepilot"
    assert isinstance(artifact, VercelInventoryArtifact)
    assert artifact.extracted_at > 0
    assert "health_summary" in data
    assert "invoicepilot" in artifact.health_summary.healthy

# SPDX-License-Identifier: Apache-2.0

from aethos_core.operations.execution.failure_diagnostic_artifact import (
    build_evidence_groups,
    enrich_failure_diagnostic_artifact,
    select_last_successful_production_deployment,
)
from aethos_core.operations.execution.execution_artifacts import ExecutionArtifact


def test_failure_diagnostic_evidence_prioritization():
    deployments = [
        {"id": "dpl_ready1", "state": "ready", "target": "production", "branch": "main", "commit": "aaa"},
        {"id": "dpl_ready2", "state": "ready", "target": "production", "branch": "main", "commit": "bbb"},
        {
            "id": "dpl_failed",
            "state": "error",
            "target": "unknown",
            "branch": "codex/fix",
            "commit": "d9ac148",
            "error_message": 'Command "npm run build" exited with 1',
        },
    ]
    groups = build_evidence_groups(
        failed_dep=deployments[2],
        last_prod=deployments[0],
        all_deployments=deployments,
        inventory_evidence=["source:vercel_api"],
        log_evidence=[],
        reachability_evidence=None,
        diagnosis_evidence=None,
        source="vercel_api",
    )
    assert len(groups["primary"]) >= 1
    assert any("npm run build" in str(i.get("message", "")) for i in groups["primary"])
    assert len(groups["historical"]) == 1
    assert len(groups["debug"]) >= 1
    assert len(groups["primary"]) < len(deployments) * 2


def test_last_successful_production_deployment_prefers_production_target():
    deps = [
        {"id": "dpl_preview", "state": "ready", "target": "preview"},
        {"id": "dpl_prod", "state": "ready", "target": "production", "commit": "abc"},
    ]
    picked = select_last_successful_production_deployment(deps)
    assert picked is not None
    assert picked["id"] == "dpl_prod"


def test_failure_diagnostic_production_impact_confidence_separate_from_failure():
    artifact = ExecutionArtifact(
        execution_id="rex-diag",
        provider="vercel",
        operation_type="why_down",
        target_name="talking-avatar-agent",
        data_source="provider_api",
    )
    enrich_failure_diagnostic_artifact(
        artifact,
        inventory_evidence=["source:vercel_api"],
        api_deployments={
            "deployments": [
                {"id": "dpl_prod_ok", "state": "ready", "target": "production", "branch": "main", "commit": "ok1"},
                {
                    "id": "dpl_failed",
                    "state": "error",
                    "target": "unknown",
                    "error_message": 'Command "npm run build" exited with 1',
                    "commit": "d9ac148",
                },
            ]
        },
        api_log_payload=None,
        prod_url="https://talking-avatar-agent.vercel.app",
        reachability={"url": "https://talking-avatar-agent.vercel.app", "reachable": True, "summary": "HTTP 200"},
    )
    diag = artifact.diagnostic
    assert diag["failure_reason_confidence"] == "confirmed"
    assert diag["production_impact_confidence"] == "insufficient_evidence"
    assert "Unclear" in diag["production_impact_summary"]
    assert diag["next_safe_checks"]


def test_failure_diagnostic_primary_deployment_first_in_report():
    from aethos_core.operations.execution.execution_artifacts import format_execution_report

    artifact = ExecutionArtifact(
        execution_id="rex-diag2",
        provider="vercel",
        operation_type="why_down",
        target_name="talking-avatar-agent",
        data_source="provider_api",
    )
    enrich_failure_diagnostic_artifact(
        artifact,
        inventory_evidence=[],
        api_deployments={
            "deployments": [
                {
                    "id": "dpl_DNDTWron",
                    "state": "error",
                    "target": "unknown",
                    "branch": "codex/do-it-all-routing-fix",
                    "commit": "d9ac148c7af3",
                    "error_message": 'Command "npm run build" exited with 1',
                }
            ]
        },
        api_log_payload=None,
        prod_url=None,
        reachability=None,
    )
    report = format_execution_report(artifact)
    assert "## Primary finding" in report
    assert "dpl_DNDTWron" in report
    assert "## Production impact" in report
    assert "## Next safe checks" in report
    assert "## Primary evidence" in report
    assert "## Debug evidence" not in report or "Debug evidence" in report

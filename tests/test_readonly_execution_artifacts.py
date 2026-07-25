# SPDX-License-Identifier: Apache-2.0

from aethos_core.operations.execution.execution_artifacts import ExecutionArtifact, format_execution_report
from aethos_core.operations.execution.execution_permissions import actions_for_operation


def test_readonly_execution_artifact_includes_auth_and_source():
    artifact = ExecutionArtifact(
        execution_id="rex-test",
        provider="vercel",
        operation_type="list_deployments",
        target_name="quotepilot",
        auth_method="api_token",
        auth_method_label="Vercel API token",
        data_source="provider_api",
    )
    report = format_execution_report(artifact)
    assert "Auth method:** Vercel API token" in report
    assert "Provider API execution" in report
    assert "No mutation performed" in report
    d = artifact.to_dict()
    assert d["data_source"] == "provider_api"


def test_list_deployments_actions():
    actions = actions_for_operation("list_deployments", provider="vercel")
    assert "vercel_api_deployments" in actions

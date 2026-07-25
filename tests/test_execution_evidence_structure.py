# SPDX-License-Identifier: Apache-2.0

from aethos_core.operations.execution.execution_artifacts import ExecutionArtifact, format_execution_report
from aethos_core.operations.execution.execution_evidence import (
    CONFIDENCE_CONFIRMED,
    evidence_from_deployment,
    evidence_from_log_payload,
    evidence_item,
)


def test_execution_artifact_serializes_evidence_and_operational_events():
    artifact = ExecutionArtifact(
        execution_id="rex-ev1",
        provider="vercel",
        operation_type="list_domains",
        target_name="invoicepilot",
        evidence=[
            evidence_item(
                source="vercel_api",
                type="domain_record",
                confidence=CONFIDENCE_CONFIRMED,
                message="invoicepilot.com · verified=True",
            )
        ],
        operational_events=[{"at": "2026-05-20T10:02:00Z", "label": "deployment created", "source": "vercel_api"}],
        confidence="confirmed",
    )
    d = artifact.to_dict()
    assert len(d["evidence"]) == 1
    assert d["evidence"][0]["source"] == "vercel_api"
    assert d["operational_events"][0]["label"] == "deployment created"
    report = format_execution_report(artifact)
    assert "## Evidence" in report
    assert "## Operational events" in report
    assert "invoicepilot.com" in report


def test_evidence_from_deployment_includes_failure_reason():
    items = evidence_from_deployment(
        {
            "id": "dpl_x",
            "state": "error",
            "target": "production",
            "branch": "main",
            "commit": "abc123",
            "error_message": "Command npm run build exited with 1",
        }
    )
    types = {i["type"] for i in items}
    assert "deployment_state" in types
    assert "failure_reason" in types


def test_evidence_from_log_payload_captures_error_events():
    items = evidence_from_log_payload(
        {
            "source": "provider_api",
            "deployment_id": "dpl_x",
            "event_count": 1,
            "events": [{"type": "stderr", "text": "Error: module not found"}],
            "log_lines": [],
        }
    )
    assert any(i["type"] == "deployment_event" for i in items)

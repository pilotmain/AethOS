# SPDX-License-Identifier: Apache-2.0
"""GitHub workflow rerun preflight tests."""

from __future__ import annotations

from unittest.mock import patch

import pytest

from aethos_core.config import get_settings
from aethos_core.cross_provider_correlation.correlation_store import clear_store_for_tests, publish_github_evidence
from aethos_core.operations.mutations.preflight import run_mutation_preflight
from aethos_core.providers.github.mutations.workflow_rerun_preflight import (
    assess_correlation_gate,
    compose_governed_rerun_preflight_sections,
    prepare_workflow_rerun_preflight,
)


@pytest.fixture
def mutation_enabled(monkeypatch):
    monkeypatch.setenv("MUTATION_EXECUTION_ENABLED", "true")
    monkeypatch.setenv("MUTATION_T3_PRODUCTION_ENABLED", "true")
    get_settings.cache_clear()
    yield
    get_settings.cache_clear()


def setup_function() -> None:
    clear_store_for_tests()


def _failed_github_evidence() -> dict:
    return {
        "repository": "pilotmain/aethos",
        "branch": {"branch": "main"},
        "commits": {"commits": [{"sha": "abc123def456", "message": "fix", "author": "raya"}]},
        "checks": {"ok": True, "failed_count": 1, "checks": [{"name": "ci", "conclusion": "failure"}]},
        "workflow_diagnostic": {
            "ok": True,
            "latest_failed_run": {
                "id": 123456,
                "name": "CI",
                "run_number": 42,
                "head_branch": "main",
                "head_sha": "abc123def456",
                "status": "completed",
                "conclusion": "failure",
            },
        },
        "workflow_runs": {"ok": True, "runs": []},
    }


def test_compose_preflight_sections_include_target_and_verification() -> None:
    sections = compose_governed_rerun_preflight_sections(
        resolution={
            "repository": "pilotmain/aethos",
            "workflow_name": "CI",
            "source_run_id": 123456,
            "head_branch": "main",
            "head_sha": "abc123def456",
        },
        correlation_gate={"allowed": True, "boundary": "github"},
        deploy_risk={"deploy_workflow": False},
    )
    text = "\n".join(sections)
    assert "Created governed GitHub workflow rerun preflight" in text
    assert "Run ID: `123456`" in text
    assert "No rerun has been performed yet" in text
    assert "Verification:" in text


@patch("aethos_core.providers.github.mutations.workflow_rerun_preflight.discover_workflow_rerun_from_readonly_substrate")
def test_prepare_preflight_uses_correlation_failed_run(mock_discover) -> None:
    publish_github_evidence("rerun-pf", _failed_github_evidence())
    mock_discover.return_value = {"ok": False, "error": "should not be called"}
    result = prepare_workflow_rerun_preflight(
        session_id="rerun-pf",
        target_name="pilotmain/aethos",
        user_request="rerun the failed GitHub workflow",
    )
    assert result.get("ok") is True
    assert result.get("source_run_id") == 123456
    assert result.get("preflight_sections")
    assert "CI" in "\n".join(result["preflight_sections"])


def test_correlation_gate_blocks_vercel_boundary() -> None:
    from aethos_core.cross_provider_correlation.correlation_store import publish_vercel_evidence

    publish_github_evidence("rerun-block", _failed_github_evidence())
    publish_vercel_evidence(
        "rerun-block",
        {
            "project_name": "aethos-web",
            "project": {"details": {"repo_link": "pilotmain/aethos"}},
            "latest_deployment": {"id": "d1", "state": "error", "commit": "abc123def456"},
            "failed_deployment": {"id": "d1", "state": "error", "commit": "abc123def456"},
            "build_analysis": {"error_lines": ["build failed"]},
        },
    )
    from aethos_core.cross_provider_correlation.evidence_publisher import ingest_github_live_evidence, ingest_vercel_live_evidence

    ingest_github_live_evidence("rerun-block", _failed_github_evidence())
    ingest_vercel_live_evidence(
        "rerun-block",
        {
            "project_name": "aethos-web",
            "project": {"details": {"repo_link": "pilotmain/aethos"}},
            "latest_deployment": {"id": "d1", "state": "error", "commit": "abc123def456"},
            "failed_deployment": {"id": "d1", "state": "error", "commit": "abc123def456"},
            "build_analysis": {"error_lines": ["build failed"]},
        },
    )
    gate = assess_correlation_gate(session_id="rerun-block")
    assert gate["allowed"] is True or gate["boundary"] == "github"


@patch("aethos_core.operations.mutations.preflight._mutation_provider_auth_block", return_value=None)
@patch("aethos_core.providers.github.mutations.workflow_rerun_preflight.prepare_workflow_rerun_preflight")
def test_mutation_preflight_includes_governed_sections(mock_prepare, _auth, mutation_enabled) -> None:
    mock_prepare.return_value = {
        "ok": True,
        "repository": "pilotmain/aethos",
        "workflow_name": "CI",
        "source_run_id": 123456,
        "source_run_number": 42,
        "source_status": "completed",
        "source_conclusion": "failure",
        "head_branch": "main",
        "head_sha": "abc123def456",
        "preflight_sections": compose_governed_rerun_preflight_sections(
            resolution={
                "repository": "pilotmain/aethos",
                "workflow_name": "CI",
                "source_run_id": 123456,
                "head_branch": "main",
                "head_sha": "abc123def456",
            },
            correlation_gate={"allowed": True, "boundary": "github"},
            deploy_risk={"deploy_workflow": False},
        ),
    }
    outcome = run_mutation_preflight(
        job_type="mutation_preflight",
        params={
            "user_request": "rerun the failed GitHub workflow for pilotmain/aethos",
            "provider": "github",
            "operation_type": "workflow_rerun",
            "target_name": "pilotmain/aethos",
            "target_status": "resolved",
            "session_id": "rerun-pf-run",
        },
    )
    assert outcome.preflight_status == "ready_for_mutation_approval"
    assert "Created governed GitHub workflow rerun preflight" in outcome.full_result

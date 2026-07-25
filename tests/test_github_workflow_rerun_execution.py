# SPDX-License-Identifier: Apache-2.0
"""GitHub workflow rerun execution tests."""

from __future__ import annotations

from unittest.mock import patch

import pytest

from aethos_core.config import get_settings
from aethos_core.operations.mutations.execution import run_mutation_execution
from aethos_core.providers.github.mutations.github_mutation_adapter import GitHubMutationAdapter
from aethos_core.providers.github.mutations.workflow_rerun import execute_workflow_rerun


@pytest.fixture
def mutation_enabled(monkeypatch):
    monkeypatch.setenv("MUTATION_EXECUTION_ENABLED", "true")
    get_settings.cache_clear()
    yield
    get_settings.cache_clear()


@patch("aethos_core.providers.github.mutations.workflow_rerun.rerun_latest_workflow")
def test_execute_workflow_rerun_delegates(mock_rerun) -> None:
    mock_rerun.return_value = {"ok": True, "operation": "workflow_rerun", "source_run_id": 1}
    result = execute_workflow_rerun(
        "token",
        repository="pilotmain/aethos",
        workflow_resolution={"source_run_id": 1, "workflow_name": "CI"},
    )
    assert result["ok"] is True
    mock_rerun.assert_called_once()


@patch("aethos_core.providers.github.mutations.github_mutation_adapter.execute_workflow_rerun")
@patch("aethos_core.operations.orchestration.provider_runtime.get_provider_api_token", return_value="token")
@patch("aethos_core.operations.orchestration.provider_runtime.resolve_execution_auth", return_value={"credential_id": "gh"})
def test_github_mutation_adapter_executes_rerun(_auth, _token, mock_execute, mutation_enabled) -> None:
    mock_execute.return_value = {"ok": True, "detail": "rerun submitted"}
    adapter = GitHubMutationAdapter()
    result = adapter.execute(
        operation="workflow_rerun",
        params={
            "target_name": "pilotmain/aethos",
            "workflow_resolution": {"source_run_id": 99, "workflow_name": "CI"},
        },
    )
    assert result["ok"] is True
    mock_execute.assert_called_once()


@patch("aethos_core.providers.github.mutations.github_mutation_adapter.execute_workflow_rerun")
@patch("aethos_core.operations.orchestration.provider_runtime.get_provider_api_token", return_value="token")
@patch("aethos_core.operations.orchestration.provider_runtime.resolve_execution_auth", return_value={"credential_id": "gh"})
def test_run_mutation_execution_reruns_after_approval(_auth, _token, mock_execute, mutation_enabled) -> None:
    mock_execute.return_value = {"ok": True, "source_run_id": 99}
    result = run_mutation_execution(
        params={
            "provider": "github",
            "operation_type": "workflow_rerun",
            "target_name": "pilotmain/aethos",
            "workflow_resolution": {"ok": True, "source_run_id": 99, "workflow_name": "CI"},
            "credential_id": "gh",
            "mutation_execution_approved": True,
            "risk_tier": "T2_low_risk_mutation",
        },
    )
    assert result.executed is True
    assert result.artifact.get("provider_result", {}).get("ok") is True
    mock_execute.assert_called_once()


def test_run_mutation_execution_never_reruns_without_approval(mutation_enabled) -> None:
    result = run_mutation_execution(
        params={
            "provider": "github",
            "operation_type": "workflow_rerun",
            "target_name": "pilotmain/aethos",
            "workflow_resolution": {"ok": True, "source_run_id": 99, "workflow_name": "CI"},
            "credential_id": "gh",
            "risk_tier": "T2_low_risk_mutation",
        },
    )
    assert result.executed is False
    assert result.dry_run is True

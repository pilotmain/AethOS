# SPDX-License-Identifier: Apache-2.0

import pytest

from aethos_core.operations.execution.execution_runner import run_local_readonly_execution


@pytest.fixture
def workspace_env(tmp_path, monkeypatch):
    root = tmp_path / "repo"
    root.mkdir()
    monkeypatch.setenv("AETHOS_WORKSPACE_ROOT", str(root))
    yield root


def test_git_status_execution(workspace_env):
    import subprocess

    subprocess.run(["git", "init"], cwd=workspace_env, check=True, capture_output=True)
    outcome = run_local_readonly_execution(
        params={
            "provider": "local",
            "operation_type": "local_workspace_fix",
            "target_name": str(workspace_env),
            "approved_actions": ["git_status", "git_branch"],
        }
    )
    assert outcome.artifact.read_only is True
    assert len(outcome.artifact.findings) >= 2
    assert "Read-only local inspection" in outcome.summary

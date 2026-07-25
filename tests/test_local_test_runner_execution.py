# SPDX-License-Identifier: Apache-2.0

import json
import pytest

from aethos_core.operations.execution.execution_runner import run_local_readonly_execution


@pytest.fixture
def workspace_env(tmp_path, monkeypatch):
    root = tmp_path / "AethOS"
    web = root / "web"
    web.mkdir(parents=True)
    (web / "package.json").write_text(
        json.dumps({"scripts": {"typecheck": "echo typecheck-ok", "test": "echo test-ok"}}),
        encoding="utf-8",
    )
    monkeypatch.setenv("AETHOS_WORKSPACE_ROOT", str(root))
    yield root


def test_package_scripts_and_npm_typecheck(workspace_env):
    outcome = run_local_readonly_execution(
        params={
            "provider": "local",
            "operation_type": "local_workspace_fix",
            "target_name": str(workspace_env),
            "approved_actions": ["package_scripts", "npm_typecheck"],
        }
    )
    scripts = next(f for f in outcome.artifact.findings if f.get("action") == "package_scripts")
    assert "typecheck" in str(scripts.get("scripts"))
    typecheck = next(f for f in outcome.artifact.findings if f.get("action") == "npm_typecheck")
    assert "typecheck-ok" in str(typecheck.get("output"))

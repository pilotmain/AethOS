# SPDX-License-Identifier: Apache-2.0

import pytest

from aethos_core.operations.local_preflight import build_local_preflight
from aethos_core.runtime.workspace_diagnostics import resolve_workspace_root


@pytest.fixture
def workspace_env(tmp_path, monkeypatch):
    root = tmp_path / "AethOS"
    root.mkdir()
    monkeypatch.setenv("AETHOS_WORKSPACE_ROOT", str(root))
    yield root


def test_local_preflight_uses_canonical_root(workspace_env):
    pf = build_local_preflight(
        operation_type="local_workspace_fix",
        user_request="check local workspace",
    )
    root = str(resolve_workspace_root())
    assert pf.target_name == root
    assert pf.current_state.get("repo_path") == root
    assert pf.current_state.get("workspace_root") == root
    assert "explicit_repo_path" not in pf.missing_information

# SPDX-License-Identifier: Apache-2.0

from aethos_core.runtime.workspace_diagnostics import get_workspace_diagnostics, repo_root


def test_workspace_diagnostics_has_core_fields():
    diag = get_workspace_diagnostics()
    assert "workspace_root" in diag
    assert "runtime_python" in diag
    assert "profile_store_path" in diag
    assert diag["repo_root"] == str(repo_root())

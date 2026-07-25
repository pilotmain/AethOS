# SPDX-License-Identifier: Apache-2.0

import pytest

from aethos_core.runtime.browser_profile_store import profiles_root_path
from aethos_core.runtime.workspace_diagnostics import resolve_workspace_root


@pytest.fixture
def workspace_env(tmp_path, monkeypatch):
    root = tmp_path / "AethOS"
    root.mkdir()
    (root / "data" / "browser_profiles").mkdir(parents=True)
    monkeypatch.setenv("AETHOS_WORKSPACE_ROOT", str(root))
    monkeypatch.setenv("BROWSER_PROFILES_DIR", str(root / "data" / "browser_profiles"))
    from aethos_core.config import get_settings

    get_settings.cache_clear()
    yield root
    get_settings.cache_clear()


def test_profile_store_under_workspace_root(workspace_env):
    assert resolve_workspace_root() == workspace_env.resolve()
    store = profiles_root_path()
    assert str(store).startswith(str(workspace_env))

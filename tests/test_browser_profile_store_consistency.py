# SPDX-License-Identifier: Apache-2.0

import json
import os
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from aethos_core.runtime.browser_profile_store import (
    BrowserProfileStore,
    browser_profile_store,
    profiles_root_path,
    store_diagnostics,
)
from aethos_core.runtime.browser_profiles import BrowserProfileStatus


@pytest.fixture
def isolated_profiles_dir(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv("BROWSER_PROFILES_DIR", str(tmp_path))
    from aethos_core.config import get_settings

    get_settings.cache_clear()
    browser_profile_store.clear_all_for_tests()
    yield tmp_path
    browser_profile_store.clear_all_for_tests()
    get_settings.cache_clear()


def _seed_profile(site: str = "vercel.com") -> str:
    return browser_profile_store.save_from_session(
        session_id="bsess-test",
        site=site,
        storage_state={"cookies": [], "origins": []},
    ).profile_id


def test_save_list_and_diagnostics_same_path(isolated_profiles_dir: Path):
    pid = _seed_profile()
    diag = store_diagnostics()
    assert diag["profile_count"] == 1
    assert diag["profiles"][0]["profile_id"] == pid
    assert diag["profiles"][0]["meta_exists"] is True
    assert diag["profiles"][0]["storage_exists"] is True
    assert str(isolated_profiles_dir) in diag["profile_store_path"]
    listed = browser_profile_store.list_all(refresh=True)
    assert len(listed) == 1
    assert listed[0].profile_id == pid


def test_get_reloads_from_disk_not_stale_cache(isolated_profiles_dir: Path):
    pid = _seed_profile()
    browser_profile_store._cache.clear()
    loaded = browser_profile_store.get(pid)
    assert loaded is not None
    assert loaded.profile_id == pid


def test_api_list_matches_store(isolated_profiles_dir: Path):
    os.environ["BROWSER_AUTOMATION_ENABLED"] = "true"
    _seed_profile()
    try:
        from aethos_core.config import get_settings

        get_settings.cache_clear()
        from aethos_core.api.main import app

        client = TestClient(app)
        body = client.get("/api/v1/browser/profiles").json()
        assert body["count"] == 1
        assert body["profile_store_path"] == str(profiles_root_path())
        assert body["profiles"][0]["profile_id"].startswith("bprof-")
    finally:
        os.environ.pop("BROWSER_AUTOMATION_ENABLED", None)
        from aethos_core.config import get_settings

        get_settings.cache_clear()


def test_profile_persists_after_new_store_instance(isolated_profiles_dir: Path):
    pid = _seed_profile()
    path = profiles_root_path()
    fresh = BrowserProfileStore()
    found = fresh.get(pid)
    assert found is not None
    assert found.status == BrowserProfileStatus.ACTIVE
    assert (path / f"{pid}.json").is_file()
    assert (path / f"{pid}.storage.json").is_file()
    meta = json.loads((path / f"{pid}.json").read_text(encoding="utf-8"))
    assert meta["profile_id"] == pid

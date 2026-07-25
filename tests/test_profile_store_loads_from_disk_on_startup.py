# SPDX-License-Identifier: Apache-2.0

import json

from aethos_core.runtime.browser_profile_store import (
    browser_profile_store,
    load_profiles_from_disk_at_startup,
)


def test_profile_store_loads_from_disk_on_startup(tmp_path, monkeypatch):
    root = tmp_path / "browser_profiles"
    root.mkdir()
    profile_id = "bprof-deadbeef1234"
    meta = {
        "profile_id": profile_id,
        "site": "vercel.com",
        "scope": "vercel",
        "storage_path": str(root / f"{profile_id}.storage.json"),
        "created_at": 1.0,
        "status": "active",
        "read_only_allowed": True,
        "write_actions_allowed": False,
        "user_approved_persistence": True,
        "persistence_mode": "persistent",
        "expires_at": None,
    }
    (root / f"{profile_id}.json").write_text(json.dumps(meta), encoding="utf-8")
    (root / f"{profile_id}.storage.json").write_text('{"cookies": []}', encoding="utf-8")
    monkeypatch.setenv("BROWSER_PROFILES_DIR", str(root))
    from aethos_core.config import get_settings

    get_settings.cache_clear()

    browser_profile_store._cache.clear()
    info = load_profiles_from_disk_at_startup()
    assert info["profile_count"] == 1
    assert profile_id in info["profile_ids"]
    loaded = browser_profile_store.get(profile_id)
    assert loaded is not None
    assert loaded.persistence_mode == "persistent"

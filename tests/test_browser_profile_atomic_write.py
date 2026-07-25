# SPDX-License-Identifier: Apache-2.0

import json

from aethos_core.runtime.browser_profile_store import BrowserProfileStore, _storage_path


def test_atomic_write_creates_valid_storage_file(tmp_path, monkeypatch):
    monkeypatch.setenv("BROWSER_PROFILES_DIR", str(tmp_path))
    from aethos_core.config import get_settings

    get_settings.cache_clear()
    store = BrowserProfileStore()
    store.clear_all_for_tests()
    profile = store.save_from_session(
        session_id="bsess-atomic",
        site="vercel.com",
        storage_state={"cookies": [{"name": "test", "value": "x", "domain": ".vercel.com"}], "origins": []},
    )
    path = _storage_path(profile.profile_id)
    assert path.is_file()
    assert not path.with_name(path.name + ".tmp").exists()
    data = json.loads(path.read_text(encoding="utf-8"))
    assert data["cookies"]

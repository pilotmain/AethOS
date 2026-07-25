# SPDX-License-Identifier: Apache-2.0

import os
import tempfile

from aethos_core.runtime.browser_profile_store import browser_profile_store
from aethos_core.runtime.browser_profiles import BrowserProfileStatus


def test_no_profile_saved_by_default():
    browser_profile_store.clear_all_for_tests()
    assert browser_profile_store.list_all() == []


def test_save_and_list_profile():
    browser_profile_store.clear_all_for_tests()
    profile = browser_profile_store.save_from_session(
        session_id="bsess-test",
        site="vercel.com",
        storage_state={"cookies": [], "origins": []},
    )
    assert profile.profile_id.startswith("bprof-")
    assert profile.site == "vercel.com"
    assert profile.scope == "vercel"
    assert profile.read_only_allowed is True
    assert profile.write_actions_allowed is False
    listed = browser_profile_store.list_all()
    assert len(listed) == 1
    public = listed[0].to_public_dict()
    assert "cookie" not in public["storage_path"].lower() or public["storage_path"].startswith("(")

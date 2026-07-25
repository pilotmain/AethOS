# SPDX-License-Identifier: Apache-2.0

from fastapi.testclient import TestClient

from aethos_core.runtime.browser_profile_store import browser_profile_store


def test_forget_removes_profile():
    from aethos_core.api.main import app

    browser_profile_store.clear_all_for_tests()
    profile = browser_profile_store.save_from_session(
        session_id="bsess-x",
        site="vercel.com",
        storage_state={"cookies": []},
    )
    client = TestClient(app)
    r = client.post(f"/api/v1/browser/profiles/{profile.profile_id}/forget")
    assert r.status_code == 200
    assert client.get("/api/v1/browser/profiles").json()["count"] == 0

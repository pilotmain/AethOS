# SPDX-License-Identifier: Apache-2.0

from fastapi.testclient import TestClient

from tests.browser_test_utils import reset_browser_test_state


def test_login_dashboard_no_credential_request():
    from aethos_core.api.main import app

    client = TestClient(app)
    r = client.post(
        "/api/v1/chat",
        json={
            "message": "login to vercel.com and check my dashboard",
            "session_id": "p8-login",
        },
    )
    reply = r.json()["reply"].lower()
    assert "enter your password" not in reply
    assert "provide your password" not in reply
    assert "i checked your dashboard" not in reply
    assert "i checked" not in reply
    assert "manual" in reply or "supervised" in reply
    reset_browser_test_state()


def test_session_store_has_no_credential_fields():
    from aethos_core.runtime.browser_lifecycle import BrowserSessionStatus
    from aethos_core.runtime.browser_session import BrowserSession

    s = BrowserSession(
        id="bsess-test",
        target="vercel.com",
        url="https://vercel.com",
        status=BrowserSessionStatus.RUNNING,
    )
    d = s.to_dict()
    assert "password" not in d
    assert "cookie" not in d
    assert "credential" not in d

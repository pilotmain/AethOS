# SPDX-License-Identifier: Apache-2.0

from fastapi.testclient import TestClient

from tests.browser_test_utils import reset_browser_test_state, use_mock_browser_driver


def test_browser_status_includes_session_fields():
    from aethos_core.api.main import app

    client = TestClient(app)
    body = client.get("/api/v1/browser/status").json()
    assert "active_session" in body
    assert "active_session_count" in body
    assert body["requires_approval"] is True
    assert body["supports_login_sessions"] == "supervised_only"
    reset_browser_test_state()


def test_browser_status_available_when_mock_enabled():
    from aethos_core.api.main import app

    use_mock_browser_driver(installed=True)
    try:
        client = TestClient(app)
        body = client.get("/api/v1/browser/status").json()
        assert body["enabled"] is True
        assert body["execution_implemented"] is True
        assert body["available"] is True
        assert body["provider"] == "playwright"
    finally:
        reset_browser_test_state()

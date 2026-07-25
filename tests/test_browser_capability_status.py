# SPDX-License-Identifier: Apache-2.0

from fastapi.testclient import TestClient


def test_browser_status_endpoint_safe_shape():
    from aethos_core.api.main import app

    client = TestClient(app)
    r = client.get("/api/v1/browser/status")
    assert r.status_code == 200
    body = r.json()
    assert body["enabled"] is False or body["enabled"] is True
    assert "available" in body
    assert body["provider"] in {"none", "playwright", "future"}
    assert body["requires_approval"] is True
    assert body["supports_login_sessions"] == "supervised_only"
    assert body["status_label"] in {"Off", "Ready", "Not installed"}
    assert body["env_var"] == "BROWSER_AUTOMATION_ENABLED"
    assert "foundation_label" in body
    assert "execution_label" in body
    assert "execution_implemented" in body
    assert "diagnostics" in body
    assert body["diagnostics"]["python_executable"]
    assert body["playwright_package"] in {"installed", "missing"}
    assert body["chromium_browser"] in {"installed", "missing"}
    assert body["supports_login_sessions"] == "supervised_only"


def test_settings_includes_browser_capability():
    from aethos_core.api.main import app

    client = TestClient(app)
    r = client.get("/api/v1/settings")
    assert r.status_code == 200
    cap = r.json().get("browser_capability")
    assert cap is not None
    assert cap["requires_approval"] is True


def test_browser_off_chat_status(monkeypatch):
    from aethos_core.api.main import app
    from aethos_core.config import get_settings

    monkeypatch.setenv("BROWSER_AUTOMATION_ENABLED", "false")
    get_settings.cache_clear()
    get_settings()
    client = TestClient(app)
    r = client.post(
        "/api/v1/chat",
        json={"message": "can you use browser automation?", "session_id": "br-status-1"},
    )
    body = r.json()
    assert r.status_code == 200
    reply = body["reply"].lower()
    assert "browser" in reply
    assert "off" in reply or "not" in reply or "setup" in reply
    assert "logged in" not in reply
    assert "i logged" not in reply
    get_settings.cache_clear()
    get_settings()

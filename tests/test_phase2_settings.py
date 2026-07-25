# SPDX-License-Identifier: Apache-2.0

from fastapi.testclient import TestClient


def test_settings_endpoint():
    from aethos_core.api.main import app

    client = TestClient(app)
    r = client.get("/api/v1/settings")
    assert r.status_code == 200
    body = r.json()
    assert body["response_mode"] == "deterministic_first"
    assert "use_real_llm" in body
    assert "model" in body
    assert "browser_automation_enabled" in body
    assert "host_executor_enabled" in body


def test_settings_independent_of_chat():
    from aethos_core.api.main import app

    client = TestClient(app)
    chat = client.post("/api/v1/chat", json={"message": "hi", "session_id": "mc"})
    settings = client.get("/api/v1/settings")
    assert chat.status_code == 200
    assert settings.status_code == 200

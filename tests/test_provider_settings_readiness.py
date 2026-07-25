# SPDX-License-Identifier: Apache-2.0

from fastapi.testclient import TestClient


def test_provider_readiness_shape():
    from aethos_core.api.main import app

    client = TestClient(app)
    r = client.get("/api/v1/settings/provider")
    assert r.status_code == 200
    body = r.json()
    assert "full_reasoning" in body
    fr = body["full_reasoning"]
    assert fr["status"] in ("Ready", "Not configured")
    assert "ready" in fr
    assert fr["provider"]
    assert fr["model"]
    assert "flags" in body
    assert "use_real_llm" in body["flags"]
    assert "anthropic_key_set" in body["flags"]
    assert isinstance(body["requirements"], list)
    assert len(body["requirements"]) == 3
    assert body["deterministic_note"]
    assert body["template_fallback_note"]
    assert body["user_message"]
    assert body["setup_steps"]


def test_provider_readiness_no_secret_leak(monkeypatch):
    monkeypatch.setenv("ANTHROPIC_API_KEY", "")
    monkeypatch.setenv("USE_REAL_LLM", "false")
    monkeypatch.setenv("ACTIVE_PROVIDER", "none")
    from aethos_core.config import get_settings

    get_settings.cache_clear()
    from aethos_core.api.main import app

    client = TestClient(app)
    body = client.get("/api/v1/settings/provider").json()
    raw = str(body).lower()
    assert "sk-ant" not in raw
    assert body["flags"]["anthropic_key_set"] is False
    for req in body.get("requirements") or []:
        assert req.get("value") != body.get("anthropic_api_key")
    get_settings.cache_clear()


def test_settings_and_provider_independent_of_chat():
    from aethos_core.api.main import app

    client = TestClient(app)
    chat = client.post("/api/v1/chat", json={"message": "hi", "session_id": "p21"})
    provider = client.get("/api/v1/settings/provider")
    settings = client.get("/api/v1/settings")
    assert chat.status_code == 200
    assert provider.status_code == 200
    assert settings.status_code == 200

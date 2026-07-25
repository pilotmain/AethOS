# SPDX-License-Identifier: Apache-2.0
"""Stable contract for GET /api/v1/settings/provider."""

from fastapi.testclient import TestClient


def test_provider_settings_contract():
    from aethos_core.api.main import app

    client = TestClient(app)
    r = client.get("/api/v1/settings/provider")
    assert r.status_code == 200
    body = r.json()

    assert "full_reasoning" in body
    fr = body["full_reasoning"]
    assert isinstance(fr["ready"], bool)
    assert fr["status"] in ("Ready", "Not configured")
    assert isinstance(fr["provider"], str)
    assert isinstance(fr["model"], str)

    assert "flags" in body
    assert isinstance(body["flags"]["use_real_llm"], bool)
    assert isinstance(body["flags"]["anthropic_key_set"], bool)

    assert isinstance(body["requirements"], list)
    assert len(body["requirements"]) >= 3
    for req in body["requirements"]:
        assert "key" in req
        assert "ok" in req or "met" in req

    assert "user_message" in body
    assert "sk-ant" not in str(body).lower()

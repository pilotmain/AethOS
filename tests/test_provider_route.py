# SPDX-License-Identifier: Apache-2.0
"""Provider route — template fallback and optional Anthropic."""

from __future__ import annotations

from unittest.mock import patch

from fastapi.testclient import TestClient


def test_generative_uses_template_when_provider_off(monkeypatch):
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    monkeypatch.setenv("USE_REAL_LLM", "false")
    monkeypatch.setenv("ACTIVE_PROVIDER", "none")
    from aethos_core.config import get_settings

    get_settings.cache_clear()
    from aethos_core.api.main import app

    client = TestClient(app)
    r = client.post(
        "/api/v1/chat",
        json={
            "message": "Tell me about quantum computing for a graduate exam in full detail.",
            "session_id": "g1",
        },
    )
    assert r.status_code == 200
    body = r.json()
    assert body["used_llm"] is False
    assert body["reply"].strip()
    assert body["intent"] == "generative_answer"
    assert "Generative mode (provider not configured)" not in body["reply"]
    get_settings.cache_clear()


@patch("aethos_core.chat.service.complete_chat")
def test_generative_delegates_to_provider(mock_complete):
    from aethos_core.api.main import app
    from aethos_core.provider.completion import ProviderResult

    mock_complete.return_value = ProviderResult(
        text="Architecture overview from provider.",
        provider="anthropic",
        model="claude-test",
        used_llm=True,
    )
    client = TestClient(app)
    r = client.post(
        "/api/v1/chat",
        json={
            "message": "Tell me about quantum computing for a graduate exam in full detail.",
            "session_id": "g2",
        },
    )
    assert r.status_code == 200
    body = r.json()
    assert body["used_llm"] is True
    assert "Architecture overview" in body["reply"]
    mock_complete.assert_called_once()

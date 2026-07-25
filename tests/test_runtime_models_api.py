# SPDX-License-Identifier: Apache-2.0
"""Runtime model catalog API."""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient


@pytest.fixture(autouse=True)
def _llm_enabled(monkeypatch):
    from aethos_core.config import get_settings

    monkeypatch.setenv("USE_REAL_LLM", "true")
    monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key")
    monkeypatch.setenv("ANTHROPIC_MODEL", "claude-sonnet-4-6")
    get_settings.cache_clear()
    yield
    get_settings.cache_clear()


def test_runtime_models_endpoint():
    from aethos_core.api.main import app

    client = TestClient(app)
    response = client.get("/api/v1/runtime/models", params={"session_id": "operator"})
    assert response.status_code == 200
    body = response.json()
    assert body["ok"] is True
    assert any(row["id"] == "default" for row in body["models"])
    assert body["effective"]["provider"] == "anthropic"


def test_session_model_override_endpoint():
    from aethos_core.api.main import app

    client = TestClient(app)
    sid = "model-api-test"
    put = client.put(
        f"/api/v1/runtime/sessions/{sid}/model-override",
        json={"catalog_id": "anthropic:claude-opus-4-6"},
    )
    assert put.status_code == 200
    assert put.json()["ok"] is True
    assert put.json()["effective"]["model"] == "claude-opus-4-6"

    snapshot = client.get("/api/v1/runtime/models", params={"session_id": sid}).json()
    assert snapshot["session_override"] == "anthropic:claude-opus-4-6"

    delete = client.delete(f"/api/v1/runtime/sessions/{sid}/model-override")
    assert delete.status_code == 200
    assert delete.json()["ok"] is True

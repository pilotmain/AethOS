# SPDX-License-Identifier: Apache-2.0

from fastapi.testclient import TestClient


def test_runtime_status_shape():
    from aethos_core.api.main import app

    client = TestClient(app)
    r = client.get("/api/v1/runtime/status")
    assert r.status_code == 200
    body = r.json()
    assert body["status"] in ("ok", "degraded")
    assert "chat_ready" in body
    assert body["api_port"] == 8010
    assert "provider" in body
    assert "real_llm" in body["provider"]
    assert "ready" in body["provider"]
    assert "capabilities" in body
    assert "browser_automation" in body["capabilities"]


def test_runtime_status_no_provider_required():
    from aethos_core.api.main import app

    client = TestClient(app)
    r = client.get("/api/v1/runtime/status")
    assert r.status_code == 200
    assert isinstance(r.json()["chat_ready"], bool)

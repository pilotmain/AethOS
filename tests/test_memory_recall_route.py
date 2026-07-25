# SPDX-License-Identifier: Apache-2.0

from fastapi.testclient import TestClient

from aethos_core.api.main import app


def test_memory_recall_route(monkeypatch, tmp_path) -> None:
    monkeypatch.setenv("VECTOR_MEMORY_ENABLED", "true")
    from aethos_core.config import get_settings
    import aethos_core.memory.vector_store as vs

    get_settings.cache_clear()
    monkeypatch.setattr(vs, "_memory_path", lambda: tmp_path / "vector_memory.json")
    vs.remember(text="aethos railway deploy succeeded", tags=["deploy"])

    client = TestClient(app)
    res = client.post("/api/v1/runtime/memory/recall", json={"query": "railway deploy", "limit": 3})
    assert res.status_code == 200
    body = res.json()
    assert body["ok"] is True
    assert len(body.get("matches") or []) >= 1
    get_settings.cache_clear()

# SPDX-License-Identifier: Apache-2.0

from fastapi.testclient import TestClient

from aethos_core.api.main import app
from aethos_core.chat.chat_thread_store import get_chat_thread, upsert_chat_thread


def test_chat_thread_store_roundtrip(tmp_path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    saved = upsert_chat_thread(
        session_id="sess-test1",
        title="Deploy chat",
        messages=[{"id": "1", "role": "user", "content": "hello"}],
    )
    assert saved["ok"] is True
    row = get_chat_thread("sess-test1")
    assert row is not None
    assert row["thread"]["title"] == "Deploy chat"
    assert len(row["thread"]["messages"]) == 1


def test_chat_threads_api(tmp_path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    client = TestClient(app)
    put = client.put(
        "/api/v1/chat/threads/sess-api1",
        json={"title": "API thread", "messages": [{"id": "m1", "role": "user", "content": "hi"}]},
    )
    assert put.status_code == 200
    listed = client.get("/api/v1/chat/threads")
    assert listed.status_code == 200
    body = listed.json()
    assert body["count"] >= 1
    detail = client.get("/api/v1/chat/threads/sess-api1")
    assert detail.status_code == 200
    assert detail.json()["thread"]["messages"][0]["content"] == "hi"

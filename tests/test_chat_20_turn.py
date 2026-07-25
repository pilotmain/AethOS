# SPDX-License-Identifier: Apache-2.0
"""20-turn mixed chat reliability gate (API-level)."""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

TURNS = [
    "hi",
    "what can you do",
    "what model are you using",
    "can you access terminal",
    "please login to vercel.com",
    "what do you need from me to check Vercel",
    "explain AethOS architecture",
    "what should AethOS build first",
    "draft an MVP roadmap",
    "summarize this session",
    "How should we prioritize reliability versus new features in the first release?",
    "can you deploy this to Vercel?",
    "what is the runtime status",
    "how do I set up AethOS locally",
    "write a short product positioning paragraph for AethOS",
    "what provider is configured",
    "can you login to websites",
    "give me three coding best practices for this codebase",
    "what deployment options should we support first",
    "thanks — what are the next steps?",
]


def test_twenty_turn_chat_completes(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv("AUTH_ENABLED", "false")
    monkeypatch.setenv("MULTI_TENANT_ENABLED", "false")
    from aethos_core.config import get_settings

    get_settings.cache_clear()
    from aethos_core.api.main import app

    client = TestClient(app)
    for i, prompt in enumerate(TURNS):
        r = client.post("/api/v1/chat", json={"message": prompt, "session_id": "reliability"})
        assert r.status_code == 200, (i, prompt, r.text)
        body = r.json()
        assert isinstance(body["reply"], str), (i, prompt)
        assert body["reply"].strip(), (i, prompt)
        assert body["terminal"] is True, (i, prompt)

# SPDX-License-Identifier: Apache-2.0
"""Phase 1.1 browser prompt coverage — all 20 smoke prompts must be useful."""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from aethos_core.chat.deterministic import GENERIC_FALLBACK_MARKER

BROWSER_SMOKE_PROMPTS = [
    "hi",
    "what can you do?",
    "what model are you using?",
    "can you access terminal?",
    "can you login to vercel.com?",
    "what do you need from me to check Vercel?",
    "can you deploy to Vercel?",
    "explain AethOS architecture",
    "what should AethOS build first?",
    "draft an MVP roadmap",
    "how should AethOS stay fast and reliable?",
    "what happens if Anthropic is not configured?",
    "can you restart AethOS?",
    "can you use browser automation?",
    "what channels should AethOS support later?",
    "how should Mission Control work?",
    "what makes AethOS different?",
    "summarize the current project direction",
    "write a simple test checklist",
    "what should we do next?",
]

PROMPTS_8_20 = BROWSER_SMOKE_PROMPTS[7:]


@pytest.fixture
def client() -> TestClient:
    from aethos_core.api.main import app

    return TestClient(app)


@pytest.mark.parametrize("prompt", BROWSER_SMOKE_PROMPTS)
def test_browser_prompt_useful_reply(client: TestClient, prompt: str) -> None:
    r = client.post("/api/v1/chat", json={"message": prompt, "session_id": "phase1_1"})
    assert r.status_code == 200, r.text
    body = r.json()
    reply = (body.get("reply") or "").strip()
    assert reply, prompt
    assert body["terminal"] is True, prompt
    assert GENERIC_FALLBACK_MARKER not in reply, prompt
    assert "Configure `USE_REAL_LLM=true` and `ANTHROPIC_API_KEY`" not in reply, prompt


@pytest.mark.parametrize("prompt", PROMPTS_8_20)
def test_prompts_8_20_are_deterministic(client: TestClient, prompt: str) -> None:
    from aethos_core.chat.lanes import is_deterministic_lane

    assert is_deterministic_lane(prompt), prompt
    r = client.post("/api/v1/chat", json={"message": prompt, "session_id": "phase1_1_det"})
    body = r.json()
    assert body["used_llm"] is False, prompt
    assert body["provider"] in {None, "none"}, prompt


def test_provider_settings_endpoint(client: TestClient) -> None:
    r = client.get("/api/v1/settings/provider")
    assert r.status_code == 200
    body = r.json()
    assert "configured" in body
    assert "setup_steps" in body
    assert len(body["setup_steps"]) == 3


def test_prompt_20_next_steps_guidance(client: TestClient) -> None:
    r = client.post(
        "/api/v1/chat",
        json={"message": "what should we do next?", "session_id": "gate_20"},
    )
    body = r.json()
    reply = body["reply"]
    assert body["terminal"] is True
    assert body["used_llm"] is False
    assert "Phase 1.1" in reply
    assert "Phase 2" in reply
    assert "Mission Control" in reply
    assert GENERIC_FALLBACK_MARKER not in reply
    assert "Do not add advanced" in reply or "Do not add advanced features" in reply


def test_prompt_17_differentiation_exact(client: TestClient) -> None:
    r = client.post(
        "/api/v1/chat",
        json={"message": "what makes AethOS different?", "session_id": "gate_17"},
    )
    body = r.json()
    reply = body["reply"]
    assert body["terminal"] is True
    assert body["used_llm"] is False
    assert "chat-first" in reply.lower() or "Chat-first" in reply
    assert GENERIC_FALLBACK_MARKER not in reply
    assert "ANTHROPIC_API_KEY" not in reply


@pytest.mark.parametrize(
    "prompt",
    [
        "what makes AethOS unique?",
        "why AethOS?",
        "hat makes AethOS different?",
    ],
)
def test_differentiation_variants(client: TestClient, prompt: str) -> None:
    from aethos_core.chat.lanes import is_deterministic_lane

    assert is_deterministic_lane(prompt), prompt
    r = client.post("/api/v1/chat", json={"message": prompt, "session_id": "gate_17_var"})
    body = r.json()
    reply = (body.get("reply") or "").strip()
    assert reply
    assert body["used_llm"] is False
    assert GENERIC_FALLBACK_MARKER not in reply
    assert "different" in reply.lower() or "chat-first" in reply.lower()


def test_generative_fallback_is_helpful_not_boilerplate() -> None:
    from aethos_core.provider.completion import generative_fallback

    result = generative_fallback("Tell me about quantum computing in detail")
    assert GENERIC_FALLBACK_MARKER not in result.text
    assert "MVP-level answer" in result.text or "try a capability" in result.text
    assert "ANTHROPIC_API_KEY" in result.text

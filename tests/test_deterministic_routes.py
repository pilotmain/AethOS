# SPDX-License-Identifier: Apache-2.0
"""Deterministic lane coverage."""

from __future__ import annotations

import pytest

from aethos_core.chat.lanes import is_deterministic_lane


@pytest.mark.parametrize(
    "prompt",
    [
        "hi",
        "what can you do",
        "what model are you using",
        "can you access terminal",
        "please login to vercel.com and give me a report of all the services health?",
        "what do you need from me to check Vercel",
        "runtime status",
        "how do I set up AethOS locally",
        "can you login to websites",
        "can you deploy this to Vercel?",
    ],
)
def test_deterministic_lane_detection(prompt: str) -> None:
    assert is_deterministic_lane(prompt), prompt


@pytest.mark.parametrize(
    "prompt",
    [
        "explain AethOS architecture",
        "draft an MVP roadmap",
        "what should AethOS build first?",
        "can you restart AethOS?",
        "what happens if Anthropic is not configured?",
    ],
)
def test_project_template_lane_detection(prompt: str) -> None:
    assert is_deterministic_lane(prompt), prompt


@pytest.mark.parametrize(
    "prompt",
    [
        "Tell me about quantum entanglement in exhaustive detail for a physics exam",
    ],
)
def test_generative_lane_detection(prompt: str) -> None:
    assert not is_deterministic_lane(prompt)


def test_vercel_login_terminal_reply():
    from fastapi.testclient import TestClient

    from aethos_core.api.main import app

    client = TestClient(app)
    r = client.post(
        "/api/v1/chat/deterministic",
        json={
            "message": "please login to vercel.com and give me a report of all the services health?",
            "session_id": "t1",
        },
    )
    assert r.status_code == 200
    body = r.json()
    assert body["terminal"] is True
    assert body["provider_stream"] is False
    assert isinstance(body["reply"], str)
    assert "vercel" in body["reply"].lower()

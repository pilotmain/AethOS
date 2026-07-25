# SPDX-License-Identifier: Apache-2.0
"""Tests for Phase 9.8B — Browser Evidence Engine."""

from __future__ import annotations

import json
import os
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient

from aethos_core.browser.runtime.browser_evidence_intents import infer_browser_evidence_job
from aethos_core.browser.runtime.browser_policy import evaluate_capture_request
from aethos_core.chat.lanes import is_deterministic_lane
from aethos_core.runtime.authority import authority
from aethos_core.runtime.job_executor import job_executor


@pytest.fixture
def browser_evidence_env(monkeypatch, tmp_path):
    root = tmp_path / "browser_artifacts"
    monkeypatch.setenv("BROWSER_ARTIFACTS_DIR", str(root))
    monkeypatch.setenv("BROWSER_AUTOMATION_ENABLED", "true")
    monkeypatch.setenv("BROWSER_CAPTURE_APPROVAL_REQUIRED", "false")
    from aethos_core.config import get_settings

    get_settings.cache_clear()
    yield root
    get_settings.cache_clear()


def _mock_capture_payload():
    return {
        "ok": True,
        "metadata": {
            "title": "Example",
            "url": "https://useinvoicepilot.com/",
            "status_code": 200,
            "headings": ["h1: Invoice Pilot"],
            "links_sample": [],
            "forms_detected": 0,
        },
        "screenshot_bytes": b"\x89PNG\r\n\x1a\n",
        "dom_snapshot": {"title": "Example", "url": "https://useinvoicepilot.com/"},
        "console_logs": [{"type": "warning", "text": "demo"}],
        "network_failures": [],
    }


@patch("aethos_core.runtime.browser_runtime.run_playwright_on_browser_thread")
def test_browser_capture_creates_artifacts_audit(mock_thread, browser_evidence_env):
    mock_thread.side_effect = lambda fn, timeout=120.0: fn()

    with patch(
        "aethos_core.browser.runtime.browser_capture.capture_page_evidence",
        return_value=_mock_capture_payload(),
    ):
        from aethos_core.browser.runtime.browser_runtime import run_browser_evidence_capture

        result = run_browser_evidence_capture(
            url="https://useinvoicepilot.com",
            capture_type="screenshot",
            user_request="capture screenshot of useinvoicepilot.com",
        )

    assert result["ok"] is True
    assert len(result["artifacts"]) >= 3
    types = {a["artifact_type"] for a in result["artifacts"]}
    assert "browser_screenshot" in types
    assert "browser_page_metadata" in types

    audit_path = browser_evidence_env / "browser_audit.jsonl"
    assert audit_path.is_file()
    row = json.loads(audit_path.read_text(encoding="utf-8").strip().splitlines()[-1])
    assert row["action"] == "browser_capture"
    assert row["result"] == "success"
    assert row["policy_tier"] == "T1"


def test_policy_blocks_hidden_interaction(browser_evidence_env):
    policy = evaluate_capture_request(
        url="https://example.com",
        capture_type="screenshot",
        user_request="click deploy button automatically",
    )
    assert policy["allowed"] is False
    assert policy["failure_class"] == "blocked_interaction"

    from aethos_core.browser.runtime.browser_runtime import run_browser_evidence_capture

    result = run_browser_evidence_capture(
        url="https://example.com",
        capture_type="screenshot",
        user_request="click deploy button automatically",
    )
    assert result["ok"] is False
    assert result["blocked"] is True
    denial = result["artifacts"][0]
    assert denial["artifact_type"] == "browser_policy_denial"


def test_metadata_only_capture_type(browser_evidence_env):
    job = infer_browser_evidence_job("inspect page metadata for pilotmain.com")
    assert job is not None
    assert job[0] == "browser_capture_execution"
    assert job[1]["capture_type"] == "metadata"


@patch("aethos_core.runtime.browser_runtime.run_playwright_on_browser_thread")
def test_chat_job_execution_path(mock_thread, browser_evidence_env):
    mock_thread.side_effect = lambda fn, timeout=120.0: fn()
    job_executor.drain_queue_for_tests()

    with patch(
        "aethos_core.browser.runtime.browser_capture.capture_page_evidence",
        return_value=_mock_capture_payload(),
    ):
        job = authority.create_job(
            title="Browser evidence",
            job_type="browser_capture_execution",
            params={
                "user_request": "capture screenshot of useinvoicepilot.com",
                "operation_type": "browser_capture",
                "capture_type": "screenshot",
                "target_url": "https://useinvoicepilot.com",
            },
            source="chat",
            session_id="web-test",
            auto_run=True,
        )
        assert job_executor.drain_once_for_tests()

    from aethos_core.runtime.jobs import job_store

    finished = job_store.get(job.id)
    assert finished is not None
    assert finished.status.value == "completed"
    assert "browser_screenshot" in (finished.full_result or "")


@patch("aethos_core.provider.completion.complete_chat")
def test_browser_evidence_deterministic_lane(mock_complete, browser_evidence_env):
    mock_complete.side_effect = AssertionError("provider must not run")
    from aethos_core.api.main import app

    client = TestClient(app)
    msg = "capture screenshot of useinvoicepilot.com"
    assert is_deterministic_lane(msg)
    res = client.post("/api/v1/chat", json={"message": msg, "session_id": "be-test"})
    body = res.json()
    assert body["used_llm"] is False
    reply_lower = body["reply"].lower()
    assert (
        "browser evidence job" in reply_lower
        or "job-" in body["reply"]
        or "browser observation" in reply_lower
        or "screenshot captured" in reply_lower
    )


@patch("aethos_core.runtime.browser_runtime.run_playwright_on_browser_thread")
def test_browser_capture_api(mock_thread, browser_evidence_env):
    mock_thread.side_effect = lambda fn, timeout=120.0: fn()
    from aethos_core.api.main import app

    with patch(
        "aethos_core.browser.runtime.browser_capture.capture_page_evidence",
        return_value=_mock_capture_payload(),
    ):
        client = TestClient(app)
        res = client.post(
            "/api/v1/browser/capture",
            json={"url": "https://useinvoicepilot.com", "capture_type": "screenshot"},
        )
    assert res.status_code == 200
    data = res.json()
    assert data["ok"] is True
    assert any(a["artifact_type"] == "browser_screenshot" for a in data["artifacts"])

    list_res = client.get("/api/v1/browser/artifacts")
    assert list_res.status_code == 200
    assert list_res.json()["count"] >= 1


def test_channel_parity_uses_same_intent():
    from aethos_core.channels.inbound import handle_channel_message
    from aethos_core.channels.base.channel_adapter import ChannelMessage

    msg = "capture screenshot of useinvoicepilot.com"
    web_job = infer_browser_evidence_job(msg)
    assert web_job is not None
    assert web_job[0] == "browser_capture_execution"

    with patch("aethos_core.channels.inbound._maybe_pairing_gate", return_value=None):
        with patch("aethos_core.chat.service.resolve_chat_turn") as turn:
            turn.return_value = type(
                "R",
                (),
                {"reply": "job created", "intent": "browser_evidence_job_created", "used_llm": False},
            )()
            channel_msg = ChannelMessage(
                channel="telegram",
                external_user_id="u1",
                external_chat_id="123",
                text=msg,
                session_id="tg-123-99",
            )
            result = handle_channel_message(channel_msg)
    assert result.ok is True
    turn.assert_called_once_with(msg, session_id="tg-123-99", channel="telegram")

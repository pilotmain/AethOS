# SPDX-License-Identifier: Apache-2.0
"""Workspace email triage — governed drafts only (§B6)."""

from __future__ import annotations

import json

import pytest

from aethos_core.config import get_settings
from aethos_core.execution_brain.agent_tool_executor import execute_agent_tool


@pytest.fixture
def _suite(tmp_path, monkeypatch):
    monkeypatch.setenv("WORKSPACE_SUITE_STORE_DIR", str(tmp_path / "ws"))
    monkeypatch.setenv("CHANNEL_OUTBOUND_STORE_DIR", str(tmp_path / "outbound"))
    get_settings.cache_clear()
    yield
    get_settings.cache_clear()


def test_email_drafts_never_auto_send(_suite, monkeypatch):
    settings = get_settings()
    monkeypatch.setattr(settings, "workspace_suite_enabled", True)
    triage = json.loads(execute_agent_tool("workspace_email", {"action": "triage"}, session_id="default"))
    assert triage["error"] == "imap_not_configured"
    draft = json.loads(
        execute_agent_tool(
            "workspace_email",
            {"action": "draft_reply", "to": "person@example.com", "subject": "Re: hi", "body": "thanks!"},
            session_id="default",
        )
    )
    assert draft["ok"] is True
    assert draft["draft"]["sent"] is False
    monkeypatch.setattr(settings, "channel_gateway_enabled", True)
    pre = json.loads(
        execute_agent_tool(
            "workspace_email",
            {"action": "send_preflight", "draft_id": draft["draft"]["id"]},
            session_id="default",
        )
    )
    assert pre["requires_approval"] is True

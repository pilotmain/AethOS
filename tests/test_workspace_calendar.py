# SPDX-License-Identifier: Apache-2.0
"""Workspace calendar CalDAV/ICS (§B6)."""

from __future__ import annotations

import json

import pytest

from aethos_core.config import get_settings
from aethos_core.execution_brain.agent_tool_executor import execute_agent_tool


@pytest.fixture
def _suite(tmp_path, monkeypatch):
    monkeypatch.setenv("WORKSPACE_SUITE_STORE_DIR", str(tmp_path / "wsuite"))
    get_settings.cache_clear()
    yield
    get_settings.cache_clear()


def test_workspace_calendar_ics_roundtrip(_suite, monkeypatch):
    settings = get_settings()
    monkeypatch.setattr(settings, "workspace_suite_enabled", False)
    off = json.loads(execute_agent_tool("workspace_calendar", {"action": "list"}, session_id="default"))
    assert off["error"] == "workspace_suite_disabled"

    monkeypatch.setattr(settings, "workspace_suite_enabled", True)
    add = json.loads(
        execute_agent_tool(
            "workspace_calendar",
            {"action": "add", "summary": "Standup", "start": "20260604T090000Z", "end": "20260604T091500Z"},
            session_id="default",
        )
    )
    assert add["ok"] is True

    ics = (
        "BEGIN:VCALENDAR\r\nVERSION:2.0\r\nBEGIN:VEVENT\r\nUID:abc@x\r\n"
        "SUMMARY:Imported meeting\r\nDTSTART:20260605T100000Z\r\nEND:VEVENT\r\nEND:VCALENDAR"
    )
    imported = json.loads(
        execute_agent_tool("workspace_calendar", {"action": "import_ics", "ics_text": ics}, session_id="default")
    )
    assert imported["imported"] == 1

    listed = json.loads(execute_agent_tool("workspace_calendar", {"action": "list"}, session_id="default"))
    assert listed["event_count"] == 2

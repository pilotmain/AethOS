# SPDX-License-Identifier: Apache-2.0
"""Scheduled notes/tasks via governed cron bridge (§B6)."""

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


def test_workspace_notes_scheduled_governed(_suite, monkeypatch):
    settings = get_settings()
    monkeypatch.setattr(settings, "workspace_suite_enabled", False)
    off = json.loads(execute_agent_tool("workspace_notes", {"action": "note_add", "text": "x"}, session_id="default"))
    assert off["error"] == "workspace_suite_disabled"

    monkeypatch.setattr(settings, "workspace_suite_enabled", True)
    note = json.loads(execute_agent_tool("workspace_notes", {"action": "note_add", "text": "remember this"}, session_id="default"))
    assert note["ok"] is True

    task = json.loads(
        execute_agent_tool(
            "workspace_notes",
            {"action": "task_add", "text": "deploy check", "scheduled_for": "daily 9am"},
            session_id="default",
        )
    )
    assert task["ok"] is True
    assert task["task"]["scheduled_for"] == "daily 9am"
    assert task["task"]["auto_execute"] is False

    done = json.loads(
        execute_agent_tool("workspace_notes", {"action": "task_done", "task_id": task["task"]["id"]}, session_id="default")
    )
    assert done["task"]["done"] is True

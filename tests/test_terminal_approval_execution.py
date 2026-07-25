# SPDX-License-Identifier: Apache-2.0
"""Terminal approval inbox → execute → agent_send loop."""

from __future__ import annotations

from unittest.mock import patch

import pytest

from aethos_core.agents.runtime.cursor_terminal_jobs import create_governed_terminal_preflight
from aethos_core.agents.runtime.subagent_session_store import clear_subagent_sessions_for_tests, create_subagent_session
from aethos_core.mission_control.approval_inbox.approval_inbox_service import build_approval_inbox
from aethos_core.mission_control.approval_inbox.terminal_approval_execution_service import (
    execute_terminal_preflight_from_inbox,
)
from aethos_core.workspace_runtime.terminal.terminal_preflight_store import clear_terminal_preflights_for_tests


@pytest.fixture(autouse=True)
def _clean_stores():
    clear_terminal_preflights_for_tests()
    clear_subagent_sessions_for_tests()
    yield
    clear_terminal_preflights_for_tests()
    clear_subagent_sessions_for_tests()


def test_terminal_preflight_appears_in_approval_inbox():
    create_governed_terminal_preflight(command="git status", session_id="op1", workspace_hint="aethos")
    inbox = build_approval_inbox(session_id="op1")
    assert inbox.ok
    terminal_items = [i for i in inbox.items if i.get("lane") == "workspace_terminal"]
    assert len(terminal_items) == 1
    assert terminal_items[0].get("terminal_execution_enabled") is True


@patch("aethos_core.workspace_runtime.terminal.terminal_executor._run_bounded")
def test_execute_terminal_forwards_to_subagent(mock_run, monkeypatch):
    mock_run.return_value = {"ok": True, "exit_code": 0, "output": "On branch main\n", "runner": "git"}

    row = create_subagent_session(parent_session_id="op1", goal="Analyze git status for deployment")
    session_key = row["session_key"]
    create_governed_terminal_preflight(
        command="git status",
        session_id="op1",
        workspace_hint="aethos",
        subagent_session_key=session_key,
    )
    inbox = build_approval_inbox(session_id="op1")
    item = next(i for i in inbox.items if i.get("lane") == "workspace_terminal")

    with patch("aethos_core.agents.runtime.subagent_ops._run_coordination") as mock_coord:
        mock_coord.return_value = {
            "ok": True,
            "merged": {"status": "complete"},
            "report": "Git is clean.",
            "results": [],
            "plan": {"plan_id": "p1"},
            "graph": {},
        }
        result = execute_terminal_preflight_from_inbox(session_id="op1", inbox_id=item["inbox_id"])

    assert result.ok
    assert "On branch main" in result.output
    assert session_key in result.subagent_session_keys
    assert result.agent_send_results
    assert result.agent_send_results[0]["ok"] is True

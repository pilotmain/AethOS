# SPDX-License-Identifier: Apache-2.0
"""Convergence suite — agent runtime patterns (subagent sessions, skills, memory, sandbox)."""

from __future__ import annotations

import json

import pytest

from aethos_core.execution_brain.agent_context_compaction import should_compact_messages
from aethos_core.execution_brain.agent_skill_recall import recall_skills
from aethos_core.execution_brain.agent_tool_loop_detection import ToolLoopDetector, stuck_tool_result
from aethos_core.execution_brain.agent_tool_policy import is_tool_allowed


def test_tool_loop_detector_blocks_repeats():
    det = ToolLoopDetector(repeat_threshold=3)
    inp = {"provider": "vercel"}
    assert det.check_before("provider_validate", inp)[0] is False
    det.record("provider_validate", inp)
    det.record("provider_validate", inp)
    stuck, reason = det.check_before("provider_validate", inp)
    assert stuck is True
    assert "repeat" in reason
    payload = json.loads(stuck_tool_result("provider_validate", reason))
    assert payload["error"] == "tool_loop_detected"


def test_telegram_blocks_terminal_preflight():
    assert is_tool_allowed("terminal_create_preflight", channel="telegram") is False
    assert is_tool_allowed("provider_health", channel="telegram") is True
    assert is_tool_allowed("agent_spawn", channel="telegram") is True


def test_main_session_keeps_full_access(monkeypatch):
    """handoff §12 — the operator's own main session runs with full access."""
    from aethos_core.config import get_settings

    monkeypatch.setattr(get_settings(), "sandbox_nonmain_enabled", True)
    assert is_tool_allowed("provider_create_mutation_preflight", session_id="default") is True
    assert is_tool_allowed("channel_send", session_id="operator") is True


def test_nonmain_session_sandboxed_denies_mutating_tools(monkeypatch):
    """handoff §12 — non-main (subagent) sessions deny network/mutating tools by default."""
    from aethos_core.config import get_settings

    monkeypatch.setattr(get_settings(), "sandbox_nonmain_enabled", True)
    sub = "agent:operator:subagent:spawn-abc"
    assert is_tool_allowed("provider_create_mutation_preflight", session_id=sub) is False
    assert is_tool_allowed("channel_send", session_id=sub) is False
    assert is_tool_allowed("provider_inventory", session_id=sub) is True  # readonly ok


def test_sandbox_disabled_lifts_nonmain_restriction(monkeypatch):
    from aethos_core.config import get_settings

    monkeypatch.setattr(get_settings(), "sandbox_nonmain_enabled", False)
    sub = "agent:operator:subagent:spawn-abc"
    assert is_tool_allowed("provider_create_mutation_preflight", session_id=sub) is True
    # channel restriction is independent of the sandbox flag
    assert is_tool_allowed("terminal_create_preflight", channel="telegram") is False


def test_compaction_threshold():
    big = [{"role": "user", "content": "x" * 50_000}]
    assert should_compact_messages(big) is True


def test_skill_recall_gated_by_registry_flag(monkeypatch):
    """handoff §3/§21 step 5 — skill recall is gated behind SKILLS_REGISTRY_ENABLED."""
    from aethos_core.config import get_settings

    monkeypatch.setattr(get_settings(), "skills_registry_enabled", False)
    assert recall_skills(query="deployment", limit=2)["error"] == "skills_registry_disabled"


def test_skill_recall_finds_local_skills(monkeypatch):
    from aethos_core.config import get_settings

    monkeypatch.setattr(get_settings(), "skills_registry_enabled", True)
    out = recall_skills(query="deployment", limit=2)
    assert out["ok"] is True


def test_memory_recall_tool_requires_query():
    from aethos_core.execution_brain.agent_tool_executor import execute_agent_tool

    out = execute_agent_tool("memory_recall", {}, session_id="t")
    assert "query_required" in out

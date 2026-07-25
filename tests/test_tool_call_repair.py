# SPDX-License-Identifier: Apache-2.0
"""Tool-call repair and loop outcome tests (Part A §A2)."""

from __future__ import annotations

import json

from aethos_core.agents.runtime.tool_call_repair import (
    classify_loop_outcome,
    parse_tool_arguments,
    repair_result_text,
    validate_tool_call,
)


def test_parse_tool_arguments_recovers_from_bad_json():
    args, hint = parse_tool_arguments("{not json")
    assert args == {}
    assert hint is not None
    assert "invalid JSON" in hint


def test_validate_unknown_tool_returns_repair_hint():
    hint = validate_tool_call("not_a_real_tool", {}, allowed_names={"web_search", "repo_read"})
    assert hint is not None
    assert "Unknown tool" in hint


def test_repair_result_is_structured_for_model():
    payload = json.loads(repair_result_text("missing repository"))
    assert payload["ok"] is False
    assert payload["error"] == "tool_call_repair"
    assert payload["repair_hint"] == "missing repository"


def test_classify_loop_outcome_approval():
    assert classify_loop_outcome("Approve in Mission Control to continue.", tool_calls=1) == "awaiting_approval"


def test_classify_loop_outcome_tool_executed():
    assert classify_loop_outcome("Here is the inventory.", tool_calls=2) == "tool_executed"


def test_repair_budget_caps_attempts():
    from aethos_core.agents.runtime.tool_call_repair import ToolCallRepairBudget, repair_result_text

    budget = ToolCallRepairBudget(max_attempts=2)
    assert budget.allow_repair()
    budget.record_repair()
    assert budget.allow_repair()
    budget.record_repair()
    assert budget.exhausted
    payload = json.loads(repair_result_text("bad tool", exhausted=True))
    assert payload.get("repair_exhausted") is True


def test_unknown_tool_never_calls_executor():
    hint = validate_tool_call("web_search", {}, allowed_names={"web_search"})
    assert hint is None
    bad_hint = validate_tool_call("missing_tool", {}, allowed_names={"web_search"})
    assert bad_hint is not None

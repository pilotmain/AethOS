# SPDX-License-Identifier: Apache-2.0
"""Tool relevance routing: trims a large tool catalog to the query-relevant subset while
always keeping a core, never reordering/dropping under the cap, and never trimming with
no prompt — so default (disabled) behaviour is unchanged."""

from __future__ import annotations

from aethos_core.execution_brain.tool_relevance import (
    CORE_TOOL_NAMES,
    score_tool,
    select_relevant_tools,
)


def _tool(name, desc=""):
    return {"name": name, "description": desc}


_CATALOG = [
    _tool("web_search", "search the public web"),
    _tool("skill_recall", "recall operator playbooks"),
    _tool("memory_recall", "recall past conversation memory"),
    _tool("canvas_render", "render content to the canvas"),
    _tool("github_read_repo", "read a GitHub repository's files"),
    _tool("github_issues_prs", "list GitHub issues and pull requests"),
    _tool("provider_logs", "fetch deployment logs from a provider like railway"),
    _tool("provider_health", "check provider/service deployment health"),
    _tool("workspace_calendar", "read the user's calendar events"),
    _tool("workspace_email", "triage the email inbox"),
    _tool("arbiter_run", "compare an answer across multiple models"),
    _tool("research_run", "run a deep multi-source research task"),
    _tool("approval_inbox", "list pending governed approvals"),
    _tool("list_tracked_jobs", "list tracked background jobs"),
    _tool("repo_grep", "grep across repository source code"),
    _tool("model_foundry", "fine-tune and manage models"),
]


def test_no_prompt_is_noop():
    assert select_relevant_tools(_CATALOG, None, max_tools=5) == _CATALOG
    assert select_relevant_tools(_CATALOG, "   ", max_tools=5) == _CATALOG


def test_under_cap_is_noop():
    small = _CATALOG[:4]
    assert select_relevant_tools(small, "anything at all here", max_tools=10) == small


def test_github_prompt_selects_github_tools():
    out = select_relevant_tools(_CATALOG, "read the github repository and list its pull requests", max_tools=8)
    names = {t["name"] for t in out}
    assert "github_read_repo" in names
    assert "github_issues_prs" in names
    # Irrelevant heavy tools should be dropped.
    assert "model_foundry" not in names
    assert len(out) <= 8


def test_core_tools_always_kept():
    out = select_relevant_tools(_CATALOG, "check railway deployment logs and health", max_tools=8)
    names = {t["name"] for t in out}
    assert CORE_TOOL_NAMES <= names  # core always present
    assert "provider_logs" in names and "provider_health" in names


def test_output_preserves_catalog_order():
    out = select_relevant_tools(_CATALOG, "github pull requests repository", max_tools=8)
    idx = [_CATALOG.index(t) for t in out]
    assert idx == sorted(idx)


def test_scoring_prefers_name_match():
    ptoks = {"github", "repository"}
    assert score_tool(_tool("github_read_repo", "x"), ptoks) > score_tool(_tool("web_search", "github repository"), ptoks) - 1

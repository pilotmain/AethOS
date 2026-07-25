# SPDX-License-Identifier: Apache-2.0
"""Skill optimization from traces: record per-skill outcomes, then propose improvements
from recurring failure patterns. Read-only — never edits skill files."""

from __future__ import annotations

from unittest.mock import patch
from uuid import uuid4

import aethos_core.skills.optimization as opt
from aethos_core.tenancy import tenant_scope


def _t() -> str:
    # Unique tenant per test → hermetic against the shared on-disk data store.
    return f"sk-{uuid4().hex}@example.com"

_FAKE_SKILLS = [
    {"id": "check-logs", "name": "Check Logs", "description": "inspect provider logs", "path": "x", "loaded": True},
]


def test_record_and_list_traces():
    with tenant_scope(_t()), patch.object(opt, "_load_skills", return_value=_FAKE_SKILLS):
        opt.record_skill_trace("check-logs", outcome="success")
        opt.record_skill_trace("check-logs", outcome="failure", detail="railway token expired")
        traces = opt.list_skill_traces("check-logs")
    assert len(traces) == 2
    assert traces[0]["outcome"] == "failure"  # newest first


def test_proposal_surfaces_recurring_failure_pattern():
    with tenant_scope(_t()), patch.object(opt, "_load_skills", return_value=_FAKE_SKILLS):
        for _ in range(3):
            opt.record_skill_trace("check-logs", outcome="failure", detail="railway token expired again")
        opt.record_skill_trace("check-logs", outcome="success")
        proposal = opt.propose_skill_optimization("check-logs", use_llm=False)
    assert proposal["ok"] and proposal["trace_count"] == 4 and proposal["failure_count"] == 3
    terms = {p["term"] for p in proposal["failure_patterns"]}
    assert "railway" in terms or "token" in terms
    assert any("guidance" in s.lower() for s in proposal["suggestions"])


def test_proposal_for_unknown_skill():
    with tenant_scope(_t()), patch.object(opt, "_load_skills", return_value=_FAKE_SKILLS):
        assert opt.propose_skill_optimization("nope", use_llm=False)["ok"] is False


def test_skills_with_trace_counts():
    with tenant_scope(_t()), patch.object(opt, "_load_skills", return_value=_FAKE_SKILLS):
        opt.record_skill_trace("check-logs", outcome="failure", detail="boom")
        rows = opt.skills_with_trace_counts()
    row = next(r for r in rows if r["id"] == "check-logs")
    assert row["trace_count"] == 1 and row["failure_count"] == 1

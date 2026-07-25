# SPDX-License-Identifier: Apache-2.0
"""FIX 185 — issue intake scope fidelity tests."""

from __future__ import annotations

import pytest

from aethos_core.config import get_settings
from aethos_core.software_delivery.issue_intake_scope_fidelity_service import (
    assess_plan_scope_fidelity,
    extract_issue_scope_fidelity,
)
from aethos_core.software_delivery.issue_plan_service import (
    analyze_github_issue,
    approve_implementation_planning,
    create_implementation_plan,
)
from aethos_core.software_delivery.issue_plan_store import clear_for_tests, load_issue_plan_for_session

DOC_TARGET = "docs/AETHOS_DOGFOOD_AND_PILOT_VALIDATION_PRINCIPLE.md"


@pytest.fixture(autouse=True)
def _clean():
    clear_for_tests()
    get_settings.cache_clear()
    yield
    clear_for_tests()
    get_settings.cache_clear()


def test_extract_issue_scope_fidelity_from_dogfood_issue_1_body():
    issue = {
        "number": 1,
        "title": "AethOS Dogfood Pilot — Add Pilot Execution Log Section",
        "body": (
            "### Scope (Bounded)\n\n"
            f"Add a new section to:\n\n`{DOC_TARGET}`\n\n"
            "**Section title:** Pilot Execution Log\n\n"
            "### Out Of Scope\n\n"
            "- workflow files\n- provider files\n- mutation files\n"
        ),
    }
    envelope = extract_issue_scope_fidelity(issue=issue)
    assert DOC_TARGET in envelope.expected_files
    assert envelope.explicit_bounded_scope is True
    assert "Pilot Execution Log" in envelope.intended_goal


def test_analyze_github_issue_1_produces_doc_scoped_plan_not_workflow_reframe():
    session = "fix-185-issue-1"
    result = analyze_github_issue(
        session_id=session,
        user_text="analyze github issue pilotmain/AethOS#1",
    )
    assert result.ok is True
    plan = result.plan
    assert DOC_TARGET in list(plan.get("affected_files") or [])
    goal = str((plan.get("governed_plan") or {}).get("goal") or "")
    assert "Fix GitHub workflow rerun resolution" not in goal
    assert "Pilot Execution Log" in goal or "Dogfood Pilot" in goal
    fidelity = assess_plan_scope_fidelity(plan=plan)
    assert fidelity.ok is True
    assert fidelity.plan_goal_divergence is False


def test_create_plan_blocked_when_plan_reframed_to_workflow_goal():
    session = "fix-185-block"
    analyze_github_issue(session_id=session, user_text="analyze github issue pilotmain/AethOS#1")
    plan = load_issue_plan_for_session(session_id=session)
    assert plan is not None
    plan["governed_plan"]["goal"] = "Fix GitHub workflow rerun resolution"
    plan["affected_files"] = [
        "aethos_core/providers/github/shared/workflow_resolution.py",
    ]
    from aethos_core.software_delivery.issue_plan_store import save_issue_plan

    save_issue_plan(plan)
    drafted = create_implementation_plan(session_id=session)
    assert drafted.ok is False
    assert "issue_intake_scope_fidelity_failed" in drafted.blockers
    assert "plan_goal_diverges_from_issue_scope" in drafted.blockers

    approved = approve_implementation_planning(
        session_id=session,
        user_text="approve implementation planning\nI approve this governed software delivery implementation plan for human review.",
    )
    assert approved.ok is False
    assert "issue_intake_scope_fidelity_failed" in approved.blockers


def test_bounded_issue_scope_generates_pilot_execution_log_doc_patch():
    from pathlib import Path

    from aethos_core.engineering.patch_runtime.patch_generator import generate_governed_patches

    repo = Path(__file__).resolve().parents[1]
    task = {
        "kind": "bounded_issue_scope",
        "proposed_fix": "AethOS Dogfood Pilot — Pilot Execution Log",
        "title": "AethOS Dogfood Pilot — Pilot Execution Log",
        "affected_files": [DOC_TARGET],
        "raw_request": "**Section title:** Pilot Execution Log",
    }
    generated = generate_governed_patches(
        repo,
        user_request="Add Pilot Execution Log section",
        task=task,
        target_files=[DOC_TARGET],
    )
    assert generated["ok"] is True
    assert DOC_TARGET in generated["files_patched"]
    patch = generated["patches"][0]
    assert "## Pilot Execution Log" in patch["new_content"]
    assert "pilotmain/AethOS#1" in patch["new_content"]
    assert "| Date | Issue | Stages Reached | PR | Operator Effort Notes |" in patch["new_content"]

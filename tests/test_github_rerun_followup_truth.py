# SPDX-License-Identifier: Apache-2.0
"""GitHub rerun follow-up truth tests."""

from __future__ import annotations

from aethos_core.providers.github.context.github_context_store import (
    clear_github_context_for_tests,
    get_github_rerun_context,
    save_github_context_from_evidence,
    save_github_rerun_context,
)
from aethos_core.providers.github.mutations.rerun_followup_router import (
    compose_github_workflow_rerun_followup_reply,
)


def setup_function() -> None:
    clear_github_context_for_tests()


def test_did_it_pass_before_rerun_says_no_rerun_yet() -> None:
    save_github_context_from_evidence(
        "followup-session",
        {
            "repository": "pilotmain/aethos",
            "repo": {"full_name": "pilotmain/aethos", "default_branch": "main"},
            "branch": {"branch": "main"},
            "commits": {"commits": []},
            "checks": {"ok": True, "failed_count": 0, "checks": []},
            "workflow_runs": {"ok": True, "runs": []},
            "workflow_diagnostic": {"ok": True, "latest_failed_run": None},
        },
    )
    reply = compose_github_workflow_rerun_followup_reply("did it pass?", session_id="followup-session")
    assert reply is not None
    body, intent, meta = reply
    assert intent == "github_workflow_rerun_followup"
    assert "No GitHub workflow rerun has been executed yet" in body
    assert "pilotmain/aethos" in body
    assert meta.get("rerun_executed") == "false"


def test_follow_up_uses_stored_repo_not_placeholder() -> None:
    save_github_rerun_context(
        "stored-session",
        {
            "rerun_target_repo": "pilotmain/aethos",
            "original_run_id": 99,
            "workflow_name": "CI",
            "verification_status": "preflight_ready",
        },
    )
    reply = compose_github_workflow_rerun_followup_reply("what failed this time?", session_id="stored-session")
    assert reply is not None
    body, _, meta = reply
    assert "owner/aethos" not in body
    assert "pilotmain/aethos" in body
    assert meta.get("repository") == "pilotmain/aethos"


def test_no_owner_aethos_placeholder_appears() -> None:
    save_github_context_from_evidence(
        "truth-session",
        {
            "repository": "pilotmain/aethos",
            "repo": {"full_name": "pilotmain/aethos", "default_branch": "main"},
            "branch": {"branch": "main"},
            "commits": {"commits": []},
            "checks": {"ok": True, "failed_count": 0, "checks": []},
            "workflow_runs": {"ok": True, "runs": []},
            "workflow_diagnostic": {"ok": True},
        },
    )
    reply = compose_github_workflow_rerun_followup_reply("did the workflow rerun?", session_id="truth-session")
    assert reply is not None
    body, _, _ = reply
    assert "owner/aethos" not in body
    assert "owner/repo" not in body


def test_rerun_context_persisted_after_preflight() -> None:
    save_github_rerun_context(
        "persist-session",
        {
            "rerun_target_repo": "pilotmain/aethos",
            "original_run_id": 123456,
            "workflow_name": "CI",
            "branch": "main",
            "commit_sha": "abc123def456",
            "preflight_job_id": "job-pf-1",
            "verification_status": "preflight_ready",
        },
    )
    ctx = get_github_rerun_context("persist-session")
    assert ctx is not None
    assert ctx["rerun_target_repo"] == "pilotmain/aethos"
    assert ctx["original_run_id"] == 123456
    assert ctx["preflight_job_id"] == "job-pf-1"

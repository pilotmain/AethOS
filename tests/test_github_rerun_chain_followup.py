# SPDX-License-Identifier: Apache-2.0
"""GitHub rerun chain follow-up tests."""

from __future__ import annotations

from aethos_core.providers.github.context.github_context_store import (
    clear_github_context_for_tests,
    save_github_rerun_context,
)
from aethos_core.providers.github.mutations.rerun_followup_router import compose_github_workflow_rerun_followup_reply


def setup_function() -> None:
    clear_github_context_for_tests()


def test_did_it_pass_shows_workflow_and_chain_context() -> None:
    save_github_rerun_context(
        "followup-chain",
        {
            "rerun_target_repo": "pilotmain/aethos",
            "original_run_id": 42,
            "rerun_run_id": 99,
            "rerun_outcome": "passed",
            "failure_boundary_after_rerun": "vercel",
            "chain_summary": "GitHub workflow rerun **passed**, but the correlated Vercel deployment is still failing — workflow success is not deployment success.",
            "deployment_chain": {
                "failure_boundary": "vercel",
                "workflow_passed_deploy_failed": True,
                "chain_healthy": False,
            },
        },
    )
    reply = compose_github_workflow_rerun_followup_reply("did it pass?", session_id="followup-chain")
    assert reply is not None
    body, _, _ = reply
    assert "42" in body and "99" in body
    assert "workflow success is not deployment success" in body


def test_deployment_reach_runtime_followup() -> None:
    save_github_rerun_context(
        "runtime-followup",
        {
            "rerun_target_repo": "pilotmain/aethos",
            "rerun_outcome": "passed",
            "deployment_chain": {
                "failure_boundary": "railway",
                "deploy_succeeded_runtime_unhealthy": True,
                "chain_healthy": False,
                "railway_service": "aethos-api",
            },
        },
    )
    reply = compose_github_workflow_rerun_followup_reply(
        "did deployment reach runtime?",
        session_id="runtime-followup",
    )
    assert reply is not None
    body, _, _ = reply
    assert "owner/aethos" not in body
    assert "Railway runtime is still unhealthy" in body

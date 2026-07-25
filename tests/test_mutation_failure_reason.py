# SPDX-License-Identifier: Apache-2.0
"""Mutation failure reason extraction tests."""

from __future__ import annotations

from aethos_core.operational_thread_memory.failure_reason_extractor import extract_failure_reason


def _job(**params):
    class _Job:
        def __init__(self, p):
            self.params = p

    return _Job(params)


def test_missing_credentials():
    failure = extract_failure_reason(
        _job(
            executed=False,
            execution_state="execution_failed",
            mutation_execution={
                "execution_state": "execution_failed",
                "provider_result": {"detail": "Railway API token missing from environment"},
            },
        )
    )
    assert failure is not None
    assert "credential" in failure["failure_reason"].lower()
    assert failure["failure_stage"] == "credentials"


def test_wrong_service_id():
    failure = extract_failure_reason(
        _job(
            executed=False,
            execution_state="execution_failed",
            target_resolved=False,
            mutation_execution={
                "provider_result": {"detail": "Service ID svc-invalid not found"},
            },
        )
    )
    assert failure is not None
    assert failure["failure_stage"] == "target_resolution"
    assert "not found" in failure["failure_reason"].lower() or "Service ID" in failure["failure_reason"]


def test_provider_api_rejected():
    failure = extract_failure_reason(
        _job(
            executed=False,
            execution_state="execution_failed",
            mutation_execution={
                "provider_result": {
                    "detail": "GraphQL error: permission denied",
                    "graphql_errors": [{"message": "permission denied"}],
                },
            },
        )
    )
    assert failure is not None
    assert failure["failure_stage"] == "provider_api"
    assert "permission denied" in failure["failure_reason"].lower() or "GraphQL" in failure["failure_reason"]


def test_cli_failure():
    failure = extract_failure_reason(
        _job(
            executed=False,
            execution_state="execution_failed",
            mutation_execution={
                "execution_mode": "cli",
                "provider_result": {"detail": "railway: command not found", "execution_mode": "cli"},
                "stderr": "railway: command not found",
            },
        )
    )
    assert failure is not None
    assert failure["failure_stage"] == "cli"
    assert "command not found" in failure["raw_error_excerpt"].lower() or "command not found" in failure["failure_reason"].lower()


def test_verification_failed():
    failure = extract_failure_reason(
        _job(
            executed=True,
            restart_command_submitted=True,
            restart_verification_state="restart_unverified",
            execution_state="execution_stabilizing",
        )
    )
    assert failure is not None
    assert failure["failure_stage"] == "verification"
    assert "evidence" in failure["failure_reason"].lower()


def test_github_installation_failure_message():
    failure = extract_failure_reason(
        _job(
            executed=False,
            execution_state="execution_failed",
            target_name="speakglobal-ai",
            error="No GitHub installation found for repo: rayameresa/speakglobal-ai",
        )
    )
    assert failure is not None
    assert failure["failure_stage"] == "source_binding"
    assert "rayameresa/speakglobal-ai" in failure["failure_reason"]
    assert "use pilotmain/speakglobal-ai instead" in failure["next_recommended_action"]
    assert "retry the governed restart" in failure["next_recommended_action"]


def test_github_installation_failure_message_for_pilotos():
    failure = extract_failure_reason(
        _job(
            executed=False,
            execution_state="execution_failed",
            target_name="pilotos",
            error="No GitHub installation found for repo: rayameresa/pilotos",
        )
    )
    assert failure is not None
    assert "rayameresa/pilotos" in failure["failure_reason"]
    assert "use pilotmain/pilotos instead" in failure["next_recommended_action"]


def test_logs_unavailable():
    failure = extract_failure_reason(
        _job(
            executed=True,
            restart_command_submitted=True,
            restart_verification_state="restart_unverified",
            provider_evidence_bundle={"logs_excerpt": [], "logs_unavailable": True},
        )
    )
    assert failure is not None
    assert failure["failure_stage"] == "logs"
    assert "logs" in failure["failure_reason"].lower()

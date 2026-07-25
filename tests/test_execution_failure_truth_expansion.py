# SPDX-License-Identifier: Apache-2.0
"""Execution failure truth expansion tests."""

from __future__ import annotations

from aethos_core.provider_topology.failure_truth_expander import expand_failure_truth


def _job(**params):
    class _Job:
        id = "job-fail-truth"

        def __init__(self, p):
            self.params = p

    return _Job(params)


def test_missing_railway_token():
    truth = expand_failure_truth(
        _job(
            provider="railway",
            operation_type="restart",
            target_name="speakglobal-ai",
            target={"project_name": "adequate-luck", "environment": "production", "service_name": "speakglobal-ai"},
            executed=False,
            execution_state="execution_failed",
            error="Railway API token missing from environment",
            mutation_execution={"provider_result": {"detail": "Railway API token missing from environment"}},
        )
    )
    assert truth is not None
    assert truth["failure_stage"] == "credentials"
    assert "token" in truth["failure_reason"].lower() or "credential" in truth["failure_reason"].lower()


def test_invalid_service_id():
    truth = expand_failure_truth(
        _job(
            provider="railway",
            operation_type="restart",
            target_name="speakglobal-ai",
            target={"project_name": "adequate-luck", "service_id": "svc-bad"},
            executed=False,
            execution_state="execution_failed",
            error="Service ID svc-bad not found",
        )
    )
    assert truth is not None
    assert truth["failure_stage"] == "target_resolution"


def test_provider_rejected_mutation():
    truth = expand_failure_truth(
        _job(
            provider="railway",
            operation_type="restart",
            executed=False,
            execution_state="execution_failed",
            mutation_execution={
                "provider_result": {
                    "detail": "GraphQL error: permission denied",
                    "graphql_errors": [{"message": "permission denied"}],
                }
            },
        )
    )
    assert truth is not None
    assert truth["failure_stage"] in {"railway_api", "provider_rejected"}


def test_cli_not_authenticated():
    truth = expand_failure_truth(
        _job(
            provider="railway",
            operation_type="restart",
            executed=False,
            execution_state="execution_failed",
            execution_mode="cli",
            mutation_execution={
                "execution_mode": "cli",
                "provider_result": {"detail": "railway: not authenticated", "execution_mode": "cli"},
            },
        )
    )
    assert truth is not None
    assert truth["failure_stage"] in {"railway_cli", "credentials"}


def test_source_binding_verified_but_railway_execution_fails():
    from aethos_core.provider_topology.source_binding import SourceBinding
    from aethos_core.provider_topology.topology_memory import clear_topology_for_tests, save_binding

    clear_topology_for_tests()
    save_binding(
        SourceBinding(
            provider="railway",
            project="adequate-luck",
            environment="production",
            service_name="speakglobal-ai",
            github_repo="pilotmain/speakglobal-ai",
            source_verified=True,
        )
    )
    truth = expand_failure_truth(
        _job(
            provider="railway",
            operation_type="restart",
            target_name="speakglobal-ai",
            target={"project_name": "adequate-luck", "environment": "production", "service_name": "speakglobal-ai"},
            executed=False,
            execution_state="execution_failed",
            error="Railway GraphQL mutation rejected: invalid service restart request",
            mutation_execution={"provider_result": {"detail": "Railway GraphQL mutation rejected: invalid service restart request"}},
        )
    )
    assert truth is not None
    assert truth["source_binding"]["repo"] == "pilotmain/speakglobal-ai"
    assert truth["source_binding"]["verified"] is True
    assert truth["failure_stage"] != "source_binding"

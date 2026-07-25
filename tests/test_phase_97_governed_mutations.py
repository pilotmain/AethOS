# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

from unittest.mock import patch

import pytest

from aethos_core.config import get_settings
from aethos_core.operations.mutations.blast_radius import analyze_blast_radius
from aethos_core.operations.mutations.execution import run_mutation_execution
from aethos_core.operations.mutations.mutation_execution_flow import (
    MutationExecutionError,
    approve_mutation_execution,
    validate_mutation_preflight_job,
)
from aethos_core.operations.mutations.preflight import run_mutation_preflight
from aethos_core.operations.mutations.secrets import masked_secret_reference, parse_env_var_from_request
from aethos_core.runtime.authority import authority
from aethos_core.runtime.job_executor import job_executor
from aethos_core.runtime.jobs import job_store
from tests.job_test_utils import drain_job_executor


@pytest.fixture
def mutation_enabled(monkeypatch):
    monkeypatch.setenv("MUTATION_EXECUTION_ENABLED", "true")
    monkeypatch.setenv("MUTATION_T3_PRODUCTION_ENABLED", "true")
    get_settings.cache_clear()
    yield
    get_settings.cache_clear()


def test_blast_radius_for_restart():
    br = analyze_blast_radius(
        provider="railway",
        operation_type="restart",
        target_name="speakglobal-ai",
        target_status="resolved",
    )
    assert br.production_impact is True
    assert br.reversibility == "reversible"


def test_env_var_uses_masked_secret_reference():
    parsed = parse_env_var_from_request("set Railway env var OPENAI_TIMEOUT=60 for speakglobal-ai")
    assert parsed is not None
    ref = parsed["env_var_reference"]
    assert ref["kind"] == "masked_secret_reference"
    assert ref["masked_value"] == "***"
    assert "60" not in str(ref)


def test_mutation_preflight_ready_when_enabled(mutation_enabled):
    with patch(
        "aethos_core.operations.mutations.preflight._mutation_provider_auth_block",
        return_value=None,
    ):
        outcome = run_mutation_preflight(
            job_type="mutation_preflight",
            params={
                "user_request": "restart speakglobal-ai on Railway",
                "provider": "railway",
                "operation_type": "restart",
                "target_name": "speakglobal-ai",
                "target_status": "resolved",
            },
        )
    assert outcome.preflight_status == "ready_for_mutation_approval"
    assert outcome.blast_radius.get("scope") == "production"


def test_mutation_preflight_design_only_when_disabled(monkeypatch):
    monkeypatch.setenv("MUTATION_EXECUTION_ENABLED", "false")
    monkeypatch.setenv("MUTATION_T3_PRODUCTION_ENABLED", "false")
    get_settings.cache_clear()
    outcome = run_mutation_preflight(
        job_type="mutation_preflight",
        params={
            "user_request": "restart speakglobal-ai on Railway",
            "provider": "railway",
            "operation_type": "restart",
            "target_name": "speakglobal-ai",
        },
    )
    assert outcome.preflight_status == "needs_credential"


def test_approve_mutation_requires_enabled_flag(monkeypatch):
    monkeypatch.setenv("MUTATION_EXECUTION_ENABLED", "false")
    monkeypatch.setenv("MUTATION_T3_PRODUCTION_ENABLED", "false")
    get_settings.cache_clear()
    job = authority.create_job(
        title="Mutation preflight",
        job_type="mutation_preflight",
        params={
            "user_request": "restart svc",
            "provider": "railway",
            "operation_type": "restart",
            "target_name": "svc",
            "preflight_status": "ready_for_mutation_approval",
            "risk_tier": "T2_low_risk_mutation",
            "mutation_preflight": {
                "provider": "railway",
                "operation_type": "restart",
                "target_name": "svc",
                "preflight_status": "ready_for_mutation_approval",
                "risk_tier": "T2_low_risk_mutation",
            },
        },
        source="test",
        session_id="mut-approve",
        auto_run=False,
    )
    job_store.complete_with_result(
        job.id,
        full_result="done",
        summary="done",
        preview="done",
        provider="mutation_preflight",
        model="deterministic",
        used_llm=False,
        fallback=False,
    )
    with pytest.raises(MutationExecutionError, match="not enabled"):
        validate_mutation_preflight_job(job_store.get(job.id))


def test_approve_mutation_enqueues_execution(mutation_enabled, monkeypatch):
    job = authority.create_job(
        title="GitHub workflow rerun mutation preflight",
        job_type="mutation_preflight",
        params={
            "user_request": "rerun latest workflow for AethOS",
            "provider": "github",
            "operation_type": "workflow_rerun",
            "target_name": "owner/aethos",
            "preflight_status": "ready_for_mutation_approval",
            "risk_tier": "T2_low_risk_mutation",
            "mutation_preflight": {
                "provider": "github",
                "operation_type": "workflow_rerun",
                "target_name": "owner/aethos",
                "preflight_status": "ready_for_mutation_approval",
                "risk_tier": "T2_low_risk_mutation",
                "rollback_plan": {"strategy": "rerun creates new run"},
            },
            "rollback_plan": {"strategy": "rerun creates new run"},
            "blast_radius": {"scope": "staging"},
        },
        source="test",
        session_id="mut-exec",
        auto_run=False,
    )
    job_store.complete_with_result(
        job.id,
        full_result="done",
        summary="done",
        preview="done",
        provider="mutation_preflight",
        model="deterministic",
        used_llm=False,
        fallback=False,
    )

    monkeypatch.setattr(
        "aethos_core.operations.mutations.mutation_execution_flow.stamp_execution_auth",
        lambda provider, params=None: {"credential_id": "cred-test", "auth_method": "api_token", "auth_method_label": "API token"},
    )
    monkeypatch.setattr(
        "aethos_core.providers.github.operations.mutation_adapter.GitHubMutationAdapter.execute",
        lambda self, *, operation, params: {"ok": True, "detail": "rerun ok", "operation": operation},
    )

    preflight, execution = approve_mutation_execution(job.id)
    assert preflight.params["mutation_execution_approved"] is True
    assert execution.job_type == "mutation_execution"

    job_executor.drain_queue_for_tests()
    job_executor.enqueue(execution.id)
    assert job_executor.drain_once_for_tests()

    stored = job_store.get(execution.id)
    assert stored is not None
    assert stored.params.get("executed") is True
    assert stored.params.get("verification_job_id")


def test_workflow_rerun_intent_routes_to_mutation_preflight():
    from aethos_core.operations.intents import infer_operation_preflight_intent

    out = infer_operation_preflight_intent("rerun latest workflow for AethOS")
    assert out is not None
    assert out[2]["operation_type"] == "workflow_rerun"
    assert out[2]["provider"] == "github"


def test_unapproved_mutation_execution_stays_dry_run(mutation_enabled):
    outcome = run_mutation_execution(
        params={"provider": "railway", "operation_type": "restart", "target_name": "svc"},
    )
    assert outcome.dry_run is True
    assert outcome.executed is False

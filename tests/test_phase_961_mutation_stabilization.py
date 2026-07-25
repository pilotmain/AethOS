# SPDX-License-Identifier: Apache-2.0

import pytest

from aethos_core.config import get_settings
from aethos_core.operations.intents import extract_target_hints
from aethos_core.operations.mutations.preflight_supersede import supersede_previous_mutation_preflights
from aethos_core.operations.orchestration.target_resolution import canonical_resolve_target
from aethos_core.runtime.jobs import job_store


def test_extract_target_hints_restart_on_railway():
    hints = extract_target_hints("restart speakglobal-ai on Railway")
    assert "speakglobal-ai" in hints


def test_canonical_resolve_railway_target_uses_shared_hints(monkeypatch):
    monkeypatch.setattr(
        "aethos_core.providers.railway.auth.RailwayAuthAdapter.resolve_best_auth_method",
        lambda self, operation=None: {"credential_id": "cred-1", "method": "api_token"},
    )
    monkeypatch.setattr(
        "aethos_core.providers.railway.auth.RailwayAuthAdapter.get_api_token",
        lambda self, cid: "token",
    )
    monkeypatch.setattr(
        "aethos_core.providers.railway.api_client.find_service_by_name",
        lambda token, name: {"service_id": "svc-1", "service_name": "speakglobal-ai"},
    )
    monkeypatch.setattr(
        "aethos_core.providers.railway.api_client.list_services",
        lambda token: [{"service_name": "speakglobal-ai"}],
    )
    resolution = canonical_resolve_target(
        provider="railway",
        user_request="restart speakglobal-ai on Railway",
        target_hints=[],
        operation_type="restart",
    )
    assert resolution.status == "resolved"
    assert resolution.target_name == "speakglobal-ai"


def test_mutation_preflight_supersedes_older_same_operation():
    job_store._jobs.clear()
    job_store._events.clear()
    old = job_store.create(
        title="Old mutation preflight",
        job_type="mutation_preflight",
        params={
            "provider": "railway",
            "operation_type": "restart",
            "target_name": "speakglobal-ai",
            "preflight_status": "ready_for_mutation_approval",
            "is_current": True,
        },
        session_id="s1",
        auto_run=False,
    )
    new = job_store.create(
        title="New mutation preflight",
        job_type="mutation_preflight",
        params={
            "provider": "railway",
            "operation_type": "restart",
            "target_name": "speakglobal-ai",
            "preflight_status": "ready_for_mutation_approval",
        },
        session_id="s1",
        auto_run=False,
    )
    supersede_previous_mutation_preflights(new_job_id=new.id)
    assert job_store.get(old.id).params.get("is_current") is False
    assert job_store.get(old.id).params.get("preflight_status") == "superseded"
    assert job_store.get(new.id).params.get("is_current") is True


def test_set_env_var_mutation_execution_blocked_even_when_approved(monkeypatch):
    monkeypatch.setenv("MUTATION_EXECUTION_ENABLED", "true")
    get_settings.cache_clear()
    from aethos_core.operations.mutations.execution import run_mutation_execution

    outcome = run_mutation_execution(
        params={
            "provider": "railway",
            "operation_type": "set_env_var",
            "target_name": "speakglobal-ai",
            "mutation_execution_approved": True,
        },
        job_id="job-env-block",
    )
    assert outcome.executed is False
    assert outcome.blocked is True
    assert "blocked" in outcome.full_result.lower()

# SPDX-License-Identifier: Apache-2.0
"""Mutation preflight requires resolved Railway targets before approval."""

from __future__ import annotations

from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient

from aethos_core.chat.mutation_target_chat import gate_railway_mutation_preflight
from aethos_core.config import get_settings
from aethos_core.jobs.target_resolution import resolve_target_on_job
from aethos_core.operations.mutations.mutation_execution_flow import (
    MutationExecutionError,
    validate_mutation_preflight_job,
)
from aethos_core.operations.mutations.preflight import run_mutation_preflight
from aethos_core.runtime.authority import authority
from aethos_core.runtime.job_executor import job_executor
from aethos_core.runtime.jobs import job_store
from tests.job_test_utils import drain_job_executor


@pytest.fixture(autouse=True)
def _mutation_enabled(monkeypatch):
    from aethos_core.provider_discovery.discovery_runtime import load_inventory_snapshot
    from aethos_core.provider_discovery.inventory_memory import clear_inventory_memory_for_tests
    from aethos_core.provider_discovery.provider_inventory import ProviderInventory
    from unittest.mock import patch

    monkeypatch.setenv("MUTATION_EXECUTION_ENABLED", "true")
    get_settings.cache_clear()
    clear_inventory_memory_for_tests()

    def _inventory(provider: str, max_age_minutes: int = 30):
        _ = max_age_minutes
        cached = load_inventory_snapshot(provider=provider)
        if cached and cached.projects:
            cached.freshness = "fresh"
            return cached
        return ProviderInventory(provider=provider, projects=[], freshness="unavailable")

    with patch("aethos_core.provider_discovery.discovery_runtime.get_provider_inventory", side_effect=_inventory):
        yield
    clear_inventory_memory_for_tests()
    get_settings.cache_clear()


def setup_function() -> None:
    job_store.clear_for_tests()
    job_executor.drain_queue_for_tests()


def test_unresolved_target_not_approvable():
    job = authority.create_job(
        title="Railway restart mutation preflight",
        job_type="mutation_preflight",
        params={
            "provider": "railway",
            "operation_type": "restart",
            "user_request": "Restart Railway",
            "preflight_status": "needs_information",
            "target_resolved": False,
        },
        source="test",
        auto_run=False,
    )
    stored = job_store.get(job.id)
    assert stored is not None
    stored.status = stored.status.__class__("completed")
    stored.params["mutation_preflight"] = {
        "provider": "railway",
        "operation_type": "restart",
        "preflight_status": "needs_information",
        "target_resolved": False,
    }
    with pytest.raises(MutationExecutionError, match="not approvable"):
        validate_mutation_preflight_job(stored)


def test_resolved_target_approvable_when_ready():
    job = authority.create_job(
        title="Railway restart mutation preflight",
        job_type="mutation_preflight",
        params={
            "provider": "railway",
            "operation_type": "restart",
            "target_name": "atlas-trader api",
            "target_resolved": True,
            "target": {
                "provider": "railway",
                "service_name": "atlas-trader api",
                "project_name": "atlas-trader",
                "environment": "production",
                "resolved": True,
                "confidence": 0.95,
            },
            "preflight_status": "ready_for_mutation_approval",
            "risk_tier": "T2_low_risk_mutation",
            "is_current": True,
        },
        source="test",
        auto_run=False,
    )
    stored = job_store.get(job.id)
    assert stored is not None
    stored.status = stored.status.__class__("completed")
    stored.params["mutation_preflight"] = {
        "provider": "railway",
        "operation_type": "restart",
        "target_name": "atlas-trader api",
        "target_resolved": True,
        "preflight_status": "ready_for_mutation_approval",
        "risk_tier": "T2_low_risk_mutation",
    }
    validate_mutation_preflight_job(stored)


def test_gate_blocks_ambiguous_railway_preflight():
    from aethos_core.providers.railway.target_resolver import ProviderTarget

    unresolved = ProviderTarget(
        provider="railway",
        confidence=0.0,
        resolved=False,
        candidates=[
            {"service_name": "atlas-trader api"},
            {"service_name": "atlas-trader web"},
        ],
        reason="missing_target_phrase",
    )
    with patch(
        "aethos_core.chat.mutation_target_chat.resolve_railway_provider_target",
        return_value=unresolved,
    ):
        enriched, clarification = gate_railway_mutation_preflight(
            text="Restart Railway",
            params={
                "provider": "railway",
                "operation_type": "restart",
                "user_request": "Restart Railway",
                "target_hints": [],
            },
            operation_type="restart",
        )
    assert enriched is None
    assert clarification is not None
    assert "Which Railway service" in clarification
    assert "No mutation preflight has been created yet" in clarification


def test_user_provided_target_updates_preflight():
    job = authority.create_job(
        title="Railway restart mutation preflight",
        job_type="mutation_preflight",
        params={
            "provider": "railway",
            "operation_type": "restart",
            "user_request": "Restart Railway",
            "preflight_status": "needs_information",
            "target_resolved": False,
        },
        source="test",
        auto_run=False,
    )
    stored = job_store.get(job.id)
    assert stored is not None
    stored.status = stored.status.__class__("completed")

    result = resolve_target_on_job(job_id=job.id, service_name="atlas-trader api")
    assert result["ok"] is True
    updated = job_store.get(job.id)
    assert updated is not None
    assert updated.params.get("target_resolved") is True
    assert updated.params.get("target_name") == "atlas-trader api"


def test_resolved_chat_preflight_includes_target():
    from aethos_core.api.main import app

    client = TestClient(app)
    response = client.post(
        "/api/v1/chat",
        json={"message": "Restart the Railway atlas-trader api service", "session_id": "target-required"},
    )
    body = response.json()
    assert "atlas-trader" in body["reply"]
    assert "api" in body["reply"]
    assert body.get("intent") in {"mutation_preflight_job_created", "mutation_target_clarification"}
    job_id = body.get("meta", {}).get("proposed_job_id")
    assert job_id
    drain_job_executor()
    job = job_store.get(job_id)
    assert job is not None
    assert job.params.get("target_resolved") is True
    assert job.params.get("target_name") == "atlas-trader api"
    outcome = run_mutation_preflight(job_type=job.job_type, params=job.params)
    assert outcome.target_resolved is True
    assert outcome.target_name == "atlas-trader api"

# SPDX-License-Identifier: Apache-2.0
"""Mutation approval inbox → execute governed mutation execution."""

from __future__ import annotations

import pytest

from aethos_core.config import get_settings
from aethos_core.mission_control.approval_inbox.approval_inbox_service import build_approval_inbox
from aethos_core.mission_control.approval_inbox.mutation_approval_execution_service import (
    execute_mutation_preflight_from_inbox,
)
from aethos_core.operations.mutations.taxonomy import CANONICAL_MUTATION_PREFLIGHT_JOB_TYPE
from aethos_core.runtime.jobs import job_store


@pytest.fixture(autouse=True)
def _clean_jobs(monkeypatch):
    job_store.clear_for_tests()
    get_settings.cache_clear()
    monkeypatch.setenv("MUTATION_EXECUTION_ENABLED", "true")
    monkeypatch.setenv("MUTATION_T3_PRODUCTION_ENABLED", "true")
    get_settings.cache_clear()
    yield
    job_store.clear_for_tests()
    get_settings.cache_clear()


def _seed_stop_preflight(*, session_id: str = "op-mutation-inbox") -> str:
    job = job_store.create(
        title="Railway stop mutation preflight — invoice-pilot",
        job_type=CANONICAL_MUTATION_PREFLIGHT_JOB_TYPE,
        params={
            "provider": "railway",
            "operation_type": "stop",
            "target_name": "invoice-pilot",
            "target_resolved": True,
            "target": {"resolved": True, "service_name": "invoice-pilot"},
            "preflight_status": "ready_for_mutation_approval",
            "risk_tier": "T2_low_risk_mutation",
            "mutation_preflight": {
                "provider": "railway",
                "operation_type": "stop",
                "target_name": "invoice-pilot",
                "target_resolved": True,
                "preflight_status": "ready_for_mutation_approval",
                "risk_tier": "T2_low_risk_mutation",
            },
        },
        source="chat",
        session_id=session_id,
        auto_run=False,
    )
    stored = job_store.get(job.id)
    assert stored is not None
    stored.status = stored.status.__class__("completed")
    stored.params["is_current"] = True
    return job.id


def test_mutation_preflight_appears_in_approval_inbox():
    job_id = _seed_stop_preflight()
    inbox = build_approval_inbox(session_id="op-mutation-inbox")
    assert inbox.ok
    mutation_items = [i for i in inbox.items if i.get("lane") == "governed_execution"]
    assert len(mutation_items) == 1
    assert mutation_items[0]["inbox_id"] == f"job-{job_id}"
    assert mutation_items[0].get("mutation_inbox_execution_enabled") is True


def test_execute_mutation_from_inbox_enqueues_execution():
    job_id = _seed_stop_preflight()
    inbox = build_approval_inbox(session_id="op-mutation-inbox")
    item = next(i for i in inbox.items if i.get("lane") == "governed_execution")

    result = execute_mutation_preflight_from_inbox(session_id="op-mutation-inbox", inbox_id=item["inbox_id"])

    assert result.ok
    assert result.preflight_job_id == job_id
    assert result.execution_job_id
    preflight = job_store.get(job_id)
    assert preflight.params.get("mutation_execution_approved") is True
    execution = job_store.get(result.execution_job_id)
    assert execution is not None
    assert execution.job_type == "mutation_execution"

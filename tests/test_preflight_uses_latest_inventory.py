# SPDX-License-Identifier: Apache-2.0

import pytest

from aethos_core.browser.platforms.vercel.vercel_entities import HealthState, VercelInventoryArtifact, VercelProject
from aethos_core.operations.preflight import run_operation_preflight
from aethos_core.runtime.jobs import job_store
from aethos_core.runtime.operational_memory import operational_memory


@pytest.fixture
def mem_env(tmp_path, monkeypatch):
    monkeypatch.setenv("BROWSER_PROFILES_DIR", str(tmp_path / "browser_profiles"))
    monkeypatch.setenv("CREDENTIALS_DIR", str(tmp_path / "credentials"))
    from aethos_core.security.credential_vault import reset_credential_vault_for_tests

    reset_credential_vault_for_tests()
    operational_memory.clear_for_tests()
    job_store._jobs.clear()
    job_store._events.clear()
    yield
    operational_memory.clear_for_tests()
    job_store._jobs.clear()
    job_store._events.clear()


def test_preflight_uses_latest_inventory_over_stale_memory(mem_env):
    operational_memory.record_vercel_extraction(
        VercelInventoryArtifact(
            projects=[
                VercelProject(
                    name="talking-avatar-agent",
                    health=HealthState.UNKNOWN,
                    health_confidence="unknown",
                )
            ]
        ),
        profile_id="bprof-1",
    )

    inv = VercelInventoryArtifact(
        projects=[
            VercelProject(
                name="talking-avatar-agent",
                production_url="https://talking-avatar.example",
                production_url_source="custom_domain",
                production_url_verified=True,
                health=HealthState.HEALTHY,
                health_confidence="healthy",
                production_health="healthy",
                latest_deployment_state="success",
                latest_deployment_scope="production",
                operator_status="healthy",
                url_type="custom_domain",
                evidence=["production_url_verified", "scope_detected: production"],
            )
        ]
    )

    job = job_store.create(
        title="Vercel inventory",
        job_type="vercel_projects_inventory",
        params={"vercel_inventory": inv.to_dict()},
        auto_run=False,
    )
    job_store.complete_with_result(
        job.id,
        full_result="ok",
        summary="ok",
        preview="ok",
        provider="test",
        model="test",
        used_llm=False,
        fallback=False,
    )

    outcome = run_operation_preflight(
        job_type="vercel_logs_preflight",
        params={
            "user_request": "check logs for talking-avatar-agent",
            "provider": "vercel",
            "operation_type": "check_logs",
            "target_hints": [],
        },
    )
    state = outcome.preflight.current_state
    assert state.get("production_url") == "https://talking-avatar.example"
    assert state.get("last_inventory_job_id") == job.id
    assert state.get("source") == "latest_inventory_job"

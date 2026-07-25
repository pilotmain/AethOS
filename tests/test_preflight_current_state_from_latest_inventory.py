# SPDX-License-Identifier: Apache-2.0

import pytest

from aethos_core.browser.platforms.vercel.vercel_entities import HealthState, VercelInventoryArtifact, VercelProject
from aethos_core.operations.preflight import run_operation_preflight
from aethos_core.runtime.jobs import job_store
from aethos_core.runtime.operational_memory import operational_memory


@pytest.fixture
def mem_env(tmp_path, monkeypatch):
    monkeypatch.setenv("BROWSER_PROFILES_DIR", str(tmp_path / "browser_profiles"))
    operational_memory.clear_for_tests()
    job_store._jobs.clear()
    job_store._events.clear()
    yield
    operational_memory.clear_for_tests()
    job_store._jobs.clear()
    job_store._events.clear()


def test_preflight_state_from_memory_inventory_fields(mem_env):
    p = VercelProject(
        name="talking-avatar-agent",
        production_url="https://talking.example",
        production_url_source="custom_domain",
        production_url_verified=True,
        health=HealthState.UNKNOWN,
        health_confidence="unknown",
        production_health="unknown",
        latest_deployment_state="failed",
        latest_deployment_scope="preview",
        operator_status="unknown",
        url_type="custom_domain",
        evidence=["latest_deployment_failed", "scope_detected: preview"],
    )
    operational_memory.record_vercel_extraction(
        VercelInventoryArtifact(projects=[p]),
        profile_id="bprof-1",
        last_inventory_job_id="job-mem-1",
    )
    outcome = run_operation_preflight(
        job_type="vercel_down_diagnostic_preflight",
        params={
            "user_request": "why is talking-avatar-agent down?",
            "provider": "vercel",
            "operation_type": "why_down",
            "target_hints": [],
        },
    )
    state = outcome.preflight.current_state
    assert state.get("production_url") == "https://talking.example"
    assert state.get("latest_deployment_state") == "failed"
    assert state.get("last_inventory_job_id") == "job-mem-1"
    assert state.get("evidence")

# SPDX-License-Identifier: Apache-2.0

import pytest
from fastapi.testclient import TestClient

from aethos_core.browser.platforms.vercel.vercel_entities import HealthState, VercelInventoryArtifact, VercelProject
from aethos_core.runtime.job_executor import job_executor
from aethos_core.runtime.jobs import job_store
from aethos_core.runtime.operational_memory import operational_memory
from tests.job_test_utils import drain_job_executor


@pytest.fixture
def mem_env(tmp_path, monkeypatch):
    monkeypatch.setenv("BROWSER_PROFILES_DIR", str(tmp_path / "browser_profiles"))
    operational_memory.clear_for_tests()
    job_executor.drain_queue_for_tests()
    yield
    operational_memory.clear_for_tests()
    job_executor.drain_queue_for_tests()


def _seed_quotepilot() -> None:
    operational_memory.record_vercel_extraction(
        VercelInventoryArtifact(
            projects=[
                VercelProject(
                    name="quotepilot",
                    health=HealthState.HEALTHY,
                    health_confidence="healthy",
                )
            ]
        ),
        profile_id="bprof-1",
    )


def test_redeploy_creates_preflight_not_execution(mem_env):
    from aethos_core.api.main import app

    _seed_quotepilot()
    client = TestClient(app)
    r = client.post(
        "/api/v1/chat",
        json={"message": "redeploy quotepilot", "session_id": "p92-redeploy"},
    )
    body = r.json()
    jid = (body.get("meta") or {}).get("proposed_job_id")
    assert jid and jid.startswith("job-")
    assert body["meta"]["proposed_job_type"] == "mutation_preflight"
    assert "preflight" in body["reply"].lower()
    assert "no mutation performed" in body["reply"].lower()

    drain_job_executor()
    job = job_store.get(jid)
    assert job and job.status.value == "completed"
    pf = job.params.get("mutation_preflight") or {}
    assert pf.get("target_name") == "quotepilot"
    assert pf.get("mutation_execution_enabled") is False
    assert job.params.get("execution_blocked") is True


def test_env_var_preflight_no_write(mem_env):
    from aethos_core.api.main import app

    _seed_quotepilot()
    client = TestClient(app)
    r = client.post(
        "/api/v1/chat",
        json={"message": "set NEXT_PUBLIC_API_URL for quotepilot", "session_id": "p92-env"},
    )
    jid = (r.json().get("meta") or {}).get("proposed_job_id")
    assert jid
    drain_job_executor()
    job = job_store.get(jid)
    assert job and job.job_type == "mutation_preflight"
    assert job.params.get("execution_blocked") is True

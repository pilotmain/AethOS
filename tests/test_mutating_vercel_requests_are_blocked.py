# SPDX-License-Identifier: Apache-2.0
"""Phase 9.2: mutating Vercel prompts route to preflight jobs, not execution."""

import pytest
from fastapi.testclient import TestClient

from aethos_core.browser.platforms.vercel.vercel_entities import HealthState, VercelInventoryArtifact, VercelProject
from aethos_core.runtime.job_executor import job_executor
from aethos_core.runtime.operational_memory import operational_memory
from tests.job_test_utils import drain_job_executor


@pytest.fixture(autouse=True)
def _isolate_jobs(tmp_path, monkeypatch):
    monkeypatch.setenv("BROWSER_PROFILES_DIR", str(tmp_path / "browser_profiles"))
    operational_memory.clear_for_tests()
    job_executor.drain_queue_for_tests()
    yield
    job_executor.drain_queue_for_tests()


def test_redeploy_routes_to_preflight_job():
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
    from aethos_core.api.main import app

    client = TestClient(app)
    r = client.post(
        "/api/v1/chat",
        json={"message": "redeploy quotepilot", "session_id": "p82-mut"},
    )
    body = r.json()
    reply = body["reply"].lower()
    assert "preflight" in reply
    assert "no mutation performed" in reply
    jid = (body.get("meta") or {}).get("proposed_job_id")
    assert jid and jid.startswith("job-")
    drain_job_executor()

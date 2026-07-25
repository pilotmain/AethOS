# SPDX-License-Identifier: Apache-2.0

import pytest

from aethos_core.browser.platforms.vercel.vercel_entities import HealthState, VercelInventoryArtifact, VercelProject
from aethos_core.runtime.operational_memory import operational_memory


@pytest.fixture
def mem_env(tmp_path, monkeypatch):
    monkeypatch.setenv("BROWSER_PROFILES_DIR", str(tmp_path / "browser_profiles"))
    operational_memory.clear_for_tests()
    yield
    operational_memory.clear_for_tests()


def test_inventory_persists_full_project_state(mem_env):
    p = VercelProject(
        name="talking-avatar-agent",
        production_url="https://talking-avatar.example",
        production_url_source="custom_domain",
        production_url_verified=True,
        health=HealthState.HEALTHY,
        health_confidence="healthy",
        git_repo="github.com/acme/talking-avatar-agent",
    )
    artifact = VercelInventoryArtifact(projects=[p])
    operational_memory.record_vercel_extraction(
        artifact,
        profile_id="bprof-1",
        last_inventory_job_id="job-inv-1",
    )
    mem = operational_memory.get_vercel_project_memory()["talking-avatar-agent"]
    assert mem["production_url"] == "https://talking-avatar.example"
    assert mem["operator_status"] in ("healthy", "unknown")
    assert mem["production_health"] in ("healthy", "unknown")
    assert mem["latest_deployment_state"]
    assert mem["url_type"]
    assert mem["last_inventory_job_id"] == "job-inv-1"
    assert "evidence" in mem

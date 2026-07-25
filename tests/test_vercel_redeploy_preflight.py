# SPDX-License-Identifier: Apache-2.0

import pytest

from aethos_core.browser.platforms.vercel.vercel_entities import HealthState, VercelInventoryArtifact, VercelProject
from aethos_core.operations.preflight import run_operation_preflight
from aethos_core.runtime.operational_memory import operational_memory


@pytest.fixture
def mem_env(tmp_path, monkeypatch):
    monkeypatch.setenv("BROWSER_PROFILES_DIR", str(tmp_path / "browser_profiles"))
    operational_memory.clear_for_tests()
    yield
    operational_memory.clear_for_tests()


def test_redeploy_preflight_from_memory(mem_env):
    operational_memory.record_vercel_extraction(
        VercelInventoryArtifact(
            projects=[
                VercelProject(
                    name="quotepilot",
                    production_url="https://quotepilot.example",
                    health=HealthState.HEALTHY,
                    health_confidence="healthy",
                )
            ]
        ),
        profile_id="bprof-1",
    )
    outcome = run_operation_preflight(
        job_type="vercel_redeploy_preflight",
        params={
            "user_request": "redeploy quotepilot",
            "provider": "vercel",
            "operation_type": "redeploy",
            "target_hints": [],
        },
    )
    pf = outcome.preflight
    assert pf.target_name == "quotepilot"
    assert pf.execution_enabled is False
    assert pf.required_approval is True
    assert any("mutating" in b.lower() for b in pf.blockers)
    assert "quotepilot" in outcome.summary

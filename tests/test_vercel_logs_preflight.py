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


def test_logs_preflight_notes_extraction_planned(mem_env):
    operational_memory.record_vercel_extraction(
        VercelInventoryArtifact(
            projects=[
                VercelProject(
                    name="talking-avatar-agent",
                    health=HealthState.FAILED,
                    health_confidence="failed",
                )
            ]
        ),
        profile_id="bprof-1",
    )
    outcome = run_operation_preflight(
        job_type="vercel_logs_preflight",
        params={
            "user_request": "check logs for talking-avatar-agent",
            "provider": "vercel",
            "operation_type": "check_logs",
            "target_hints": ["talking-avatar-agent"],
        },
    )
    assert outcome.preflight.target_name == "talking-avatar-agent"
    assert outcome.preflight.mutation_required is False
    assert any("log" in s.lower() for s in outcome.preflight.proposed_steps)

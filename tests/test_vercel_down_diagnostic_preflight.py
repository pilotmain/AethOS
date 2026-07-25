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


def test_down_preflight_uses_failed_signal(mem_env):
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
        job_type="vercel_down_diagnostic_preflight",
        params={
            "user_request": "why is talking-avatar-agent down?",
            "provider": "vercel",
            "operation_type": "why_down",
            "target_hints": [],
        },
    )
    pf = outcome.preflight
    assert pf.target_name == "talking-avatar-agent"
    assert pf.current_state.get("signal") in (
        "latest_deployment_failed_production_impact_unclear",
        "latest_deployment_failed_production_scope",
        "production_failure_detected",
    )
    assert pf.read_only_execution_enabled is True
    assert pf.mutation_execution_enabled is False
    assert pf.phase == "9.3B"
    assert "Phase 9.2" not in outcome.full_result
    assert "Read-only execution:** available after approval" in outcome.full_result

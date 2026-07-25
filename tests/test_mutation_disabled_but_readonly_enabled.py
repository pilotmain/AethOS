# SPDX-License-Identifier: Apache-2.0

from aethos_core.browser.platforms.vercel.vercel_entities import HealthState, VercelInventoryArtifact, VercelProject
from aethos_core.operations.preflight import run_operation_preflight
from aethos_core.runtime.operational_memory import operational_memory


def test_mutating_preflight_disables_readonly_but_keeps_mutation_disabled(tmp_path, monkeypatch):
    monkeypatch.setenv("BROWSER_PROFILES_DIR", str(tmp_path / "browser_profiles"))
    operational_memory.clear_for_tests()
    try:
        operational_memory.record_vercel_extraction(
            VercelInventoryArtifact(
                projects=[VercelProject(name="quotepilot", health=HealthState.HEALTHY, health_confidence="healthy")]
            ),
            profile_id="bprof-1",
        )
        outcome = run_operation_preflight(
            job_type="vercel_redeploy_preflight",
            params={
                "user_request": "redeploy quotepilot",
                "provider": "vercel",
                "operation_type": "redeploy",
                "target_hints": ["quotepilot"],
            },
        )
        pf = outcome.preflight
        assert pf.read_only_execution_enabled is False
        assert pf.mutation_execution_enabled is False
        assert pf.execution_enabled is False
        assert "**Read-only execution:** not available" in outcome.full_result
        assert "**Mutating execution:** disabled" in outcome.full_result
        assert "Phase 9.2" not in outcome.full_result
    finally:
        operational_memory.clear_for_tests()

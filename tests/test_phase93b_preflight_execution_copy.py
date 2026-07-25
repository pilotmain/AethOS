# SPDX-License-Identifier: Apache-2.0

from aethos_core.browser.platforms.vercel.vercel_entities import HealthState, VercelInventoryArtifact, VercelProject
from aethos_core.operations.execution_status import OPERATIONAL_PHASE
from aethos_core.operations.preflight import run_operation_preflight
from aethos_core.runtime.operational_memory import operational_memory


def test_phase93b_preflight_report_uses_phase_aware_copy(tmp_path, monkeypatch):
    monkeypatch.setenv("BROWSER_PROFILES_DIR", str(tmp_path / "browser_profiles"))
    operational_memory.clear_for_tests()
    try:
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
                "user_request": "why did talking-avatar-agent fail",
                "provider": "vercel",
                "operation_type": "why_down",
                "target_hints": ["talking-avatar-agent"],
            },
        )
        pf = outcome.preflight
        assert pf.phase == OPERATIONAL_PHASE
        assert "Phase 9.2" not in outcome.full_result
        assert "Execution enabled: no (Phase 9.2)" not in outcome.full_result
        assert "Execution remains disabled until a later phase" not in outcome.full_result
        assert "**Phase:** 9.3B" in outcome.full_result
        assert "**Read-only execution:** available after approval" in outcome.full_result
        assert "**Mutating execution:** disabled" in outcome.full_result
    finally:
        operational_memory.clear_for_tests()

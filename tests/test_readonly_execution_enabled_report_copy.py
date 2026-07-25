# SPDX-License-Identifier: Apache-2.0

from aethos_core.browser.platforms.vercel.vercel_entities import HealthState, VercelInventoryArtifact, VercelProject
from aethos_core.operations.preflight import run_operation_preflight
from aethos_core.runtime.operational_memory import operational_memory


def _seed_project(name: str, *, failed: bool = False) -> None:
    health = HealthState.FAILED if failed else HealthState.HEALTHY
    confidence = "failed" if failed else "healthy"
    operational_memory.record_vercel_extraction(
        VercelInventoryArtifact(
            projects=[VercelProject(name=name, health=health, health_confidence=confidence)]
        ),
        profile_id="bprof-1",
    )


def test_readonly_execution_enabled_for_api_capable_preflights(tmp_path, monkeypatch):
    monkeypatch.setenv("BROWSER_PROFILES_DIR", str(tmp_path / "browser_profiles"))
    operational_memory.clear_for_tests()
    try:
        cases = (
            ("why_down", "vercel_down_diagnostic_preflight", "why did lifeos fail", True),
            ("list_domains", "vercel_domains_preflight", "show domains for lifeos", False),
            ("list_deployments", "vercel_deployments_preflight", "show deployments for lifeos", False),
            ("project_details", "vercel_project_details_preflight", "show project details for lifeos", False),
        )
        for op, job_type, user_request, failed in cases:
            operational_memory.clear_for_tests()
            _seed_project("lifeos", failed=failed)
            outcome = run_operation_preflight(
                job_type=job_type,
                params={
                    "user_request": user_request,
                    "provider": "vercel",
                    "operation_type": op,
                    "target_hints": ["lifeos"],
                },
            )
            pf = outcome.preflight
            assert pf.read_only_execution_enabled is True, op
            assert pf.mutation_execution_enabled is False, op
            assert pf.approval_required is True, op
            assert "**Read-only execution:** available after approval" in outcome.full_result, op
    finally:
        operational_memory.clear_for_tests()

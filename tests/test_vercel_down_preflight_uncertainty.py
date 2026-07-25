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


def test_down_preflight_does_not_overclaim(mem_env):
    operational_memory.record_vercel_extraction(
        VercelInventoryArtifact(
            projects=[
                VercelProject(
                    name="talking-avatar-agent",
                    health=HealthState.UNKNOWN,
                    health_confidence="unknown",
                    operator_status="unknown",
                    production_health="unknown",
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
    summary = outcome.summary.lower()
    assert "not yet have enough evidence" in summary or "unclear" in summary
    assert outcome.preflight.current_state.get("signal") == "insufficient_evidence_app_is_down"

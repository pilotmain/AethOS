# SPDX-License-Identifier: Apache-2.0

import pytest

from aethos_core.browser.platforms.vercel.vercel_entities import HealthState, VercelInventoryArtifact, VercelProject
from aethos_core.operations.execution.execution_runner import run_vercel_readonly_execution
from aethos_core.runtime.operational_memory import operational_memory


@pytest.fixture
def mem_env(tmp_path, monkeypatch):
    monkeypatch.setenv("BROWSER_PROFILES_DIR", str(tmp_path / "browser_profiles"))
    operational_memory.clear_for_tests()
    yield
    operational_memory.clear_for_tests()


def test_vercel_logs_execution_uses_memory(mem_env, monkeypatch):
    operational_memory.record_vercel_extraction(
        VercelInventoryArtifact(
            projects=[
                VercelProject(
                    name="talking-avatar-agent",
                    production_url="https://example.com",
                    health=HealthState.UNKNOWN,
                    latest_deployment_state="failed",
                    evidence=["latest_deployment_failed"],
                )
            ]
        ),
        profile_id="bprof-1",
    )

    def fake_reach(url, timeout=12.0):
        return {"url": url, "reachable": True, "status_code": 200, "summary": "ok"}

    monkeypatch.setattr(
        "aethos_core.operations.execution.execution_runner._url_reachability",
        fake_reach,
    )
    outcome = run_vercel_readonly_execution(
        params={
            "provider": "vercel",
            "operation_type": "check_logs",
            "target_name": "talking-avatar-agent",
            "approved_actions": ["url_reachability", "vercel_logs_inspect"],
        }
    )
    assert outcome.artifact.read_only is True
    assert outcome.artifact.findings
    assert "talking-avatar-agent" in outcome.full_result

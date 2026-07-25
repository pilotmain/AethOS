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


def test_env_preflight_asks_value_and_environment(mem_env):
    operational_memory.record_vercel_extraction(
        VercelInventoryArtifact(
            projects=[VercelProject(name="quotepilot", health=HealthState.HEALTHY)]
        ),
        profile_id="bprof-1",
    )
    outcome = run_operation_preflight(
        job_type="vercel_env_var_preflight",
        params={
            "user_request": "set NEXT_PUBLIC_API_URL for quotepilot",
            "provider": "vercel",
            "operation_type": "set_env_var",
            "target_hints": ["quotepilot"],
        },
    )
    summary = outcome.summary
    assert "NEXT_PUBLIC_API_URL" in summary
    assert "Production" in summary or "environment" in summary.lower()
    assert "I still need" in summary

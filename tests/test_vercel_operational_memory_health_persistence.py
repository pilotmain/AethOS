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


def test_memory_persists_production_url_and_health(mem_env):
    p = VercelProject(
        name="invoicepilot",
        production_url="https://useinvoicepilot.com",
        production_url_source="custom_domain",
        health=HealthState.HEALTHY,
        health_confidence="healthy",
        known_domains=["useinvoicepilot.com"],
        git_repo="github.com/acme/invoicepilot",
    )
    artifact = VercelInventoryArtifact(projects=[p])
    operational_memory.record_vercel_extraction(artifact, profile_id="bprof-1")
    ctx = operational_memory.get_vercel_project_memory()
    entry = ctx["invoicepilot"]
    assert entry["known_production_url"] == "https://useinvoicepilot.com"
    assert entry.get("health_confidence") == "healthy"
    assert "useinvoicepilot.com" in entry.get("known_domains", [])

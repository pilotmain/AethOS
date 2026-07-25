# SPDX-License-Identifier: Apache-2.0

import pytest

from aethos_core.browser.platforms.vercel.vercel_entities import HealthState, VercelInventoryArtifact, VercelProject
from aethos_core.operations.target_resolution import resolve_vercel_target
from aethos_core.runtime.operational_memory import operational_memory


@pytest.fixture
def mem_env(tmp_path, monkeypatch):
    monkeypatch.setenv("BROWSER_PROFILES_DIR", str(tmp_path / "browser_profiles"))
    operational_memory.clear_for_tests()
    yield
    operational_memory.clear_for_tests()


def _seed(*names: str) -> None:
    projects = [
        VercelProject(name=n, health=HealthState.HEALTHY, health_confidence="healthy") for n in names
    ]
    operational_memory.record_vercel_extraction(
        VercelInventoryArtifact(projects=projects), profile_id="bprof-1"
    )


def test_resolves_exact_name(mem_env):
    _seed("quotepilot", "invoicepilot")
    r = resolve_vercel_target(user_request="redeploy quotepilot", target_hints=[])
    assert r.status == "resolved"
    assert r.target_name == "quotepilot"


def test_ambiguous_when_multiple_match(mem_env):
    _seed("talking-avatar-agent", "talking-avatar-preview")
    r = resolve_vercel_target(
        user_request="check logs for talking-avatar",
        target_hints=["talking-avatar"],
    )
    assert r.status in ("ambiguous", "resolved")


def test_missing_without_memory(mem_env, monkeypatch):
    monkeypatch.setenv("BROWSER_AUTOMATION_ENABLED", "false")
    from aethos_core.config import get_settings

    get_settings.cache_clear()
    r = resolve_vercel_target(user_request="redeploy unknown-app-xyz", target_hints=[])
    assert r.status == "missing"
    get_settings.cache_clear()

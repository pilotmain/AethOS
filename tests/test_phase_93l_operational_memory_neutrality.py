# SPDX-License-Identifier: Apache-2.0
"""Phase 9.3L — operational memory neutrality."""

from __future__ import annotations

import pytest

from aethos_core.operations.orchestration.provider_inference import find_target_in_operational_memory, infer_provider_for_hints
from aethos_core.providers.railway.target_resolver import resolve_railway_provider_target
from aethos_core.runtime.operational_memory import operational_memory


def test_railway_inventory_memory_persistence(mem_env):
    operational_memory.record_railway_inventory(
        [
            {
                "service_name": "aethos-api",
                "project_name": "pilotos",
                "service_id": "svc-1",
            }
        ],
        last_inventory_job_id="job-1",
    )
    known = operational_memory.known_railway_services()
    assert "aethos-api" in known


def test_provider_inference_uses_operational_memory(mem_env):
    operational_memory.record_railway_inventory([{"service_name": "killit-api", "project_name": "pilotos"}])
    hit = find_target_in_operational_memory("killit-api")
    assert hit is not None
    assert hit["provider"] == "railway"
    inferred = infer_provider_for_hints(["killit-api"])
    assert inferred["status"] == "resolved"
    assert inferred["provider"] == "railway"


def test_railway_target_resolver_memory_without_keyword(mem_env):
    operational_memory.record_railway_inventory([{"service_name": "aethos-api", "project_name": "pilotos"}])
    target = resolve_railway_provider_target(user_request="what about aethos-api?", target_hints=["aethos-api"])
    assert target.resolved
    assert target.service_name == "aethos-api"
    assert target.source == "operational_memory_railway"


def test_github_inventory_memory_persistence(mem_env):
    operational_memory.record_github_inventory(
        [{"full_name": "pilotmain/AethOS", "html_url": "https://github.com/pilotmain/AethOS"}]
    )
    assert "pilotmain/aethos" in operational_memory.known_github_repos()


@pytest.fixture
def mem_env(tmp_path, monkeypatch):
    monkeypatch.setenv("BROWSER_PROFILES_DIR", str(tmp_path / "browser_profiles"))
    operational_memory.clear_for_tests()
    yield
    operational_memory.clear_for_tests()

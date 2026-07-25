# SPDX-License-Identifier: Apache-2.0

import pytest

from aethos_core.browser.platforms.vercel.vercel_entities import VercelProject
from aethos_core.runtime.operational_memory import operational_memory


@pytest.fixture
def mem_env(tmp_path, monkeypatch):
    monkeypatch.setenv("BROWSER_PROFILES_DIR", str(tmp_path / "browser_profiles"))
    operational_memory.clear_for_tests()
    yield
    operational_memory.clear_for_tests()


def test_record_and_recall_vercel_projects(mem_env):
    from aethos_core.browser.platforms.vercel.vercel_entities import VercelInventoryArtifact

    operational_memory.record_vercel_extraction(
        VercelInventoryArtifact(
            projects=[
                VercelProject(name="invoicepilot"),
                VercelProject(name="lifeos"),
            ],
        ),
        profile_id="bprof-test",
    )
    known = operational_memory.known_vercel_projects()
    assert "invoicepilot" in known
    assert "lifeos" in known
    operational_memory.record_vercel_extraction(
        VercelInventoryArtifact(projects=[VercelProject(name="quotepilot")]),
        profile_id="bprof-test",
    )
    known2 = operational_memory.known_vercel_projects()
    assert "quotepilot" in known2
    assert "invoicepilot" in known2


def test_user_correction_not_project(mem_env):
    reply, applied = operational_memory.apply_user_correction("cdn is not a project")
    assert applied
    assert "cdn" in reply
    assert "cdn" not in operational_memory.known_vercel_projects()


def test_record_and_recall_railway_services(mem_env):
    operational_memory.record_railway_inventory(
        [{"service_name": "api-worker", "project_name": "backend"}],
        last_inventory_job_id="inv-1",
    )
    assert "api-worker" in operational_memory.known_railway_services()

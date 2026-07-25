# SPDX-License-Identifier: Apache-2.0

import pytest

from aethos_core.browser.platforms.vercel.vercel_entities import VercelInventoryArtifact, VercelProject
from aethos_core.runtime.operational_memory import operational_memory


@pytest.fixture
def mem_env(tmp_path, monkeypatch):
    monkeypatch.setenv("BROWSER_PROFILES_DIR", str(tmp_path / "browser_profiles"))
    operational_memory.clear_for_tests()
    yield
    operational_memory.clear_for_tests()


def test_confirm_all_projects(mem_env):
    operational_memory.record_vercel_extraction(
        VercelInventoryArtifact(
            projects=[
                VercelProject(name="quotepilot", environment="likely"),
                VercelProject(name="invoicepilot", environment="likely"),
            ]
        ),
        profile_id="bprof-1",
    )
    reply, applied = operational_memory.apply_user_correction("yes these are my vercel projects")
    assert applied
    assert "confirmed" in reply.lower()
    mem = operational_memory.get_vercel_project_memory()
    assert mem["quotepilot"].get("confirmed_by_user") is True
    assert mem["invoicepilot"].get("confirmed_by_user") is True


def test_archived_project(mem_env):
    operational_memory.record_vercel_extraction(
        VercelInventoryArtifact(projects=[VercelProject(name="wingman")]),
        profile_id="bprof-1",
    )
    reply, applied = operational_memory.apply_user_correction("wingman is archived")
    assert applied
    assert "wingman" not in operational_memory.known_vercel_projects()


def test_not_an_app_ignored(mem_env):
    operational_memory.record_vercel_extraction(
        VercelInventoryArtifact(projects=[VercelProject(name="rayameresas-projects")]),
        profile_id="bprof-1",
    )
    reply, applied = operational_memory.apply_user_correction(
        "rayameresas-projects is not an app"
    )
    assert applied
    assert "rayameresas-projects" not in operational_memory.known_vercel_projects()

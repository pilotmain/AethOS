# SPDX-License-Identifier: Apache-2.0

import json

import pytest

from aethos_core.browser.platforms.vercel.vercel_entities import VercelInventoryArtifact, VercelProject
from aethos_core.runtime.operational_memory import operational_memory


@pytest.fixture
def mem_env(tmp_path, monkeypatch):
    monkeypatch.setenv("BROWSER_PROFILES_DIR", str(tmp_path / "browser_profiles"))
    operational_memory.clear_for_tests()
    yield
    operational_memory.clear_for_tests()


def test_confirmed_projects_only_in_memory(mem_env, tmp_path):
    artifact = VercelInventoryArtifact(
        projects=[VercelProject(name="invoicepilot")],
        ignored_labels=["cdn", "workflows"],
    )
    operational_memory.record_vercel_extraction(artifact, profile_id="bprof-1")
    known = operational_memory.known_vercel_projects()
    assert "invoicepilot" in known
    assert "cdn" not in known

    from aethos_core.runtime.operational_memory import _vercel_path

    data = json.loads(_vercel_path().read_text())
    assert "cdn" in data["platforms"]["vercel"]["ignored_labels"]
    assert "invoicepilot" in data["platforms"]["vercel"]["confirmed_projects"]

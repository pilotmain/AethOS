# SPDX-License-Identifier: Apache-2.0
"""§5 — the repo ships a real starter set of operator skills, parsed correctly."""

from __future__ import annotations

from aethos_core.config import get_settings
from aethos_core.operational_skill_runtime.skill_loader import (
    get_local_operator_skill,
    load_local_operator_skills,
    reset_local_operator_skills_cache_for_tests,
)

_EXPECTED = {
    "deploy-service",
    "restart-service",
    "investigate-outage",
    "set-env-vars",
    "provision-supabase",
    "rollback-deploy",
    "check-logs",
    "review-local-repo",
}


def test_seeded_skills_load_with_name_and_description():
    reset_local_operator_skills_cache_for_tests()
    catalog = load_local_operator_skills(force=True)
    ids = {str(s["id"]) for s in catalog.get("skills") or []}
    assert _EXPECTED.issubset(ids), f"missing seeded skills: {_EXPECTED - ids}"
    by_id = {str(s["id"]): s for s in catalog["skills"]}
    for sid in _EXPECTED:
        assert by_id[sid]["name"], f"{sid} has no parsed name"
        assert by_id[sid]["description"], f"{sid} has no parsed description"
    reset_local_operator_skills_cache_for_tests()


def test_seeded_skill_detail_has_content():
    reset_local_operator_skills_cache_for_tests()
    detail = get_local_operator_skill("deploy-service")
    assert detail is not None
    assert "preflight" in (detail.get("content") or "").lower()
    reset_local_operator_skills_cache_for_tests()


def test_frontmatter_parser_tolerates_leading_header():
    from aethos_core.operational_skill_runtime.skill_loader import _read_operator_skill_frontmatter

    content = '# SPDX-License-Identifier: Apache-2.0\n"""doc"""\n\n---\nname: x\ndescription: y\n---\n'
    assert _read_operator_skill_frontmatter(content, "name") == "x"
    assert _read_operator_skill_frontmatter(content, "description") == "y"


def test_skill_recall_returns_matching_playbook():
    get_settings.cache_clear()
    if not get_settings().skills_registry_enabled:
        return  # operator disabled recall; panel still lists skills
    from aethos_core.execution_brain.agent_skill_recall import recall_skills

    out = recall_skills(query="restart service", limit=2)
    assert out["ok"] is True
    assert out["skill_count"] >= 1
    assert any(s["id"] == "restart-service" for s in out["skills"])

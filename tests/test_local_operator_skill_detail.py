# SPDX-License-Identifier: Apache-2.0

from aethos_core.operational_skill_runtime.skill_loader import (
    get_local_operator_skill,
    load_local_operator_skills,
    reset_local_operator_skills_cache_for_tests,
)


def test_get_local_operator_skill_by_id():
    reset_local_operator_skills_cache_for_tests()
    catalog = load_local_operator_skills(force=True)
    if not catalog.get("skills"):
        return
    skill_id = catalog["skills"][0]["id"]
    detail = get_local_operator_skill(str(skill_id))
    assert detail is not None
    assert detail.get("content")
    reset_local_operator_skills_cache_for_tests()

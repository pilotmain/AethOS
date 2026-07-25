# SPDX-License-Identifier: Apache-2.0
"""Multi-agent roles: architect / developer / tester / devops (and marketing) must be
recognized so a user can orchestrate a real team (the roles named in the product ask)."""

from __future__ import annotations

from aethos_core.agents.runtime.role_planning import extract_requested_roles, resolve_role_spec


def test_engineering_team_roles_parse():
    roles = extract_requested_roles(
        "orchestrate a team: one architect, one developer, one tester and one devops to ship X"
    )
    assert "Architect" in roles
    assert "Development" in roles
    assert "QA" in roles  # tester -> QA
    assert "DevOps" in roles


def test_marketing_role_parses():
    assert "Marketing" in extract_requested_roles("spawn a research and marketing agent")


def test_new_roles_have_capabilities_and_skills():
    for token, expected_display in [("architect", "Architect"), ("devops", "DevOps"), ("marketing", "Marketing")]:
        display, capability, skills = resolve_role_spec(token, attach_skills=True)
        assert display == expected_display
        assert capability
        assert len(skills) >= 1

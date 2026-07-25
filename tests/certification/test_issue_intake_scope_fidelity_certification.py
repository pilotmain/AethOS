# SPDX-License-Identifier: Apache-2.0
"""FIX 185 — issue intake scope fidelity certification."""

from __future__ import annotations

import pytest

from aethos_core.governance.governance_friction_approval_contract import FIX_185_CERTIFICATION_REQUIREMENTS
from aethos_core.software_delivery.issue_intake_scope_fidelity_contract import (
    AUTONOMOUS_PLAN_GOAL_OVERRIDE_ENABLED_FIX_185,
    AUTONOMOUS_SCOPE_EXPANSION_ENABLED_FIX_185,
    INTAKE_FIDELITY_PERFORMED_FIX_185,
    ISSUE_INTAKE_SCOPE_FIDELITY_FIX,
    ISSUE_INTAKE_SCOPE_FIDELITY_INVARIANT,
    PLAN_AUTHORITY_ENABLED_FIX_185,
)
from aethos_core.software_delivery.issue_plan_service import analyze_github_issue

pytestmark = pytest.mark.certification

DOC_TARGET = "docs/AETHOS_DOGFOOD_AND_PILOT_VALIDATION_PRINCIPLE.md"


class TestIssueIntakeScopeFidelityCertification:
    def test_fix_185_contract(self) -> None:
        assert ISSUE_INTAKE_SCOPE_FIDELITY_FIX == "FIX 185"
        assert INTAKE_FIDELITY_PERFORMED_FIX_185 is True
        assert PLAN_AUTHORITY_ENABLED_FIX_185 is False
        assert AUTONOMOUS_SCOPE_EXPANSION_ENABLED_FIX_185 is False
        assert AUTONOMOUS_PLAN_GOAL_OVERRIDE_ENABLED_FIX_185 is False
        assert "fidelity" in ISSUE_INTAKE_SCOPE_FIDELITY_INVARIANT.lower()

    def test_dogfood_issue_1_doc_scoped_plan(self) -> None:
        result = analyze_github_issue(
            session_id="fix-185-cert",
            user_text="analyze github issue pilotmain/AethOS#1",
        )
        assert result.ok is True
        plan = result.plan
        assert DOC_TARGET in list(plan.get("affected_files") or [])
        goal = str((plan.get("governed_plan") or {}).get("goal") or "")
        assert "Fix GitHub workflow rerun resolution" not in goal
        assert plan.get("issue_intake_scope_fidelity")

    def test_fix_185_certification_requirements(self) -> None:
        assert len(FIX_185_CERTIFICATION_REQUIREMENTS) >= 7

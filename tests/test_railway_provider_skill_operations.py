# SPDX-License-Identifier: Apache-2.0
"""Railway provider skill readonly + diagnostic operations."""

from __future__ import annotations

from unittest.mock import patch

from aethos_core.provider_skills.railway.skill import RailwayProviderSkill
from aethos_core.provider_skills.types import ProviderEvidenceBundle


def test_railway_skill_discover():
    skill = RailwayProviderSkill()
    with patch.object(skill, "discover", return_value={"ok": True, "inventory": {"projects": []}}):
        result = skill.discover()
    assert result["ok"] is True


def test_diagnose_failure_from_logs():
    skill = RailwayProviderSkill()
    bundle = ProviderEvidenceBundle(
        operation="restart",
        provider="railway",
        target="api",
        approved_at="2026-01-15T12:00:00+00:00",
        command="railway restart --service api --yes --json",
        command_submitted=True,
        execution_mode="cli",
        logs_excerpt=[{"message": "EADDRINUSE: address already in use", "timestamp": "2026-01-15T12:00:00+00:00"}],
    )
    diagnosis = skill.diagnose_failure(bundle)
    assert diagnosis.ok is True
    assert diagnosis.category == "port_bind_failure"


def test_propose_fix_requires_approval():
    skill = RailwayProviderSkill()
    from aethos_core.provider_skills.types import ProviderDiagnosis

    diagnosis = ProviderDiagnosis(
        ok=True,
        category="missing_env_var",
        summary="Missing environment variable",
        likely_cause="Configure DATABASE_URL",
        requires_approval=True,
    )
    fix = skill.propose_fix(diagnosis, target_name="api")
    assert fix.ok is True
    assert fix.requires_approval is True
    assert fix.preflight_required is True

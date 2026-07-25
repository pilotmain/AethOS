# SPDX-License-Identifier: Apache-2.0
"""Railway runtime diagnosis tests."""

from __future__ import annotations

from aethos_core.provider_diagnosis.railway import diagnose_railway_runtime, propose_railway_fix
from aethos_core.provider_skills.railway.skill import RailwayProviderSkill
from aethos_core.provider_skills.types import ProviderEvidenceBundle, ProviderDiagnosis


def test_missing_env_var_detected():
    result = diagnose_railway_runtime(
        logs=[{"message": "Error: DATABASE_URL environment variable is required", "timestamp": "2026-01-15T12:00:00+00:00"}],
    )
    assert result["ok"] is True
    assert result["category"] == "missing_env_var"


def test_crash_loop_detected():
    result = diagnose_railway_runtime(
        logs=[{"message": "Process exited with code 1 — container restart", "timestamp": "2026-01-15T12:00:00+00:00"}],
    )
    assert result["category"] == "crash_loop"


def test_fix_plan_generated_but_requires_approval():
    diagnosis = diagnose_railway_runtime(
        logs=[{"message": "Missing API_KEY env var", "timestamp": "2026-01-15T12:00:00+00:00"}],
    )
    plan = propose_railway_fix(diagnosis=diagnosis, target_name="api")
    assert plan["ok"] is True
    assert plan["requires_approval"] is True
    assert plan["preflight_required"] is True


def test_skill_propose_fix_requires_approval():
    skill = RailwayProviderSkill()
    bundle = ProviderEvidenceBundle(
        operation="restart",
        provider="railway",
        target="api",
        approved_at=None,
        command=None,
        command_submitted=False,
        execution_mode="cli",
        logs_excerpt=[{"message": "ECONNREFUSED database connection", "timestamp": "2026-01-15T12:00:00+00:00"}],
    )
    diagnosis = skill.diagnose_failure(bundle)
    fix = skill.propose_fix(diagnosis, target_name="api")
    assert isinstance(diagnosis, ProviderDiagnosis)
    assert fix.requires_approval is True
    assert fix.preflight_required is True

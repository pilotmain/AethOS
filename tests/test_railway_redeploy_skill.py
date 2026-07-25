# SPDX-License-Identifier: Apache-2.0
"""Railway redeploy skill tests."""

from __future__ import annotations

from aethos_core.provider_skills.railway.skill import RailwayProviderSkill
from aethos_core.provider_skills.types import ProviderEvidenceBundle


def test_redeploy_verification_requires_deployment_transition():
    skill = RailwayProviderSkill()
    bundle = ProviderEvidenceBundle(
        operation="redeploy",
        provider="railway",
        target="api",
        approved_at="2026-01-15T12:00:00+00:00",
        command="railway redeploy --service 'api' --yes --json",
        command_submitted=True,
        execution_mode="cli",
        before={"latest_deployment_id": "dep-old"},
        after={"latest_deployment_id": "dep-new"},
        evidence={"deployment_transition_detected": True, "health_confirmed": True},
    )
    result = skill.verify(operation="redeploy", before=bundle.before, after=bundle.after, evidence_bundle=bundle)
    assert result.verified is True
    assert result.status == "verified_redeploy"


def test_redeploy_unverified_without_transition():
    skill = RailwayProviderSkill()
    bundle = ProviderEvidenceBundle(
        operation="redeploy",
        provider="railway",
        target="api",
        approved_at="2026-01-15T12:00:00+00:00",
        command="railway redeploy --service 'api' --yes --json",
        command_submitted=True,
        execution_mode="cli",
        before={"latest_deployment_id": "dep-old"},
        after={"latest_deployment_id": "dep-old"},
        evidence={"deployment_transition_detected": False, "health_confirmed": True},
    )
    result = skill.verify(operation="redeploy", before=bundle.before, after=bundle.after, evidence_bundle=bundle)
    assert result.verified is False
    assert result.status == "redeploy_unverified"

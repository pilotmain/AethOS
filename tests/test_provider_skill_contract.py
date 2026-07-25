# SPDX-License-Identifier: Apache-2.0
"""Provider skill contract tests."""

from __future__ import annotations

import pytest

from aethos_core.operational_skill_runtime.contracts import ProviderSkill, skill_supports
from aethos_core.operational_skill_runtime.skill_registry import get_provider_skill


@pytest.mark.parametrize("provider", ["railway", "vercel", "github", "aws", "docker", "kubernetes"])
def test_provider_skill_exposes_core_contract(provider: str):
    skill = get_provider_skill(provider)
    assert skill is not None
    assert isinstance(skill, ProviderSkill)
    contract = skill.skill_contract()
    assert contract["provider"] == provider
    assert isinstance(contract.get("supported_operations"), list)


def test_railway_skill_supports_mutation_loop():
    skill = get_provider_skill("railway")
    assert skill is not None
    for method in ("plan", "dry_run", "execute", "collect_evidence", "verify", "diagnose_failure", "propose_fix"):
        assert skill_supports(skill, method)


def test_vercel_stub_does_not_fake_execute():
    skill = get_provider_skill("vercel")
    plan = skill.plan(operation="redeploy", target={"service_name": "demo"})
    dry = skill.dry_run(plan)
    assert dry.ok is False

# SPDX-License-Identifier: Apache-2.0
"""Central registry for provider operation skills."""

from __future__ import annotations

from typing import Any

_PROVIDERS = ("railway", "vercel", "github", "aws", "gcp", "azure", "docker", "kubernetes", "cloudflare")


def list_registered_providers() -> list[str]:
    return list(_PROVIDERS)


def get_provider_skill(provider: str):
    from aethos_core.provider_skills.runtime import load_provider_skill

    return load_provider_skill(provider)


def skill_registry_snapshot() -> dict[str, Any]:
    rows: list[dict[str, Any]] = []
    for provider in _PROVIDERS:
        skill = get_provider_skill(provider)
        if skill is None:
            rows.append({"provider": provider, "status": "missing"})
            continue
        contract = skill.skill_contract() if hasattr(skill, "skill_contract") else {}
        status = _skill_implementation_status(skill, provider)
        rows.append(
            {
                "provider": provider,
                "status": status,
                "supported_operations": contract.get("supported_operations") or getattr(skill, "supported_operations", []),
                "readonly_tools": contract.get("readonly_tools") or getattr(skill, "readonly_tools", []),
                "mutation_tools": contract.get("mutation_tools") or getattr(skill, "mutation_tools", []),
            }
        )
    return {"providers": rows, "count": len(rows)}


def _skill_implementation_status(skill: Any, provider: str) -> str:
    from aethos_core.provider_skills.stub import StubProviderSkill

    if isinstance(skill, StubProviderSkill):
        return "stub"
    discover = skill.discover(force=False)
    if discover.get("ok"):
        return "implemented"
    if provider in {"railway", "vercel", "github", "aws", "gcp", "azure", "docker", "kubernetes", "cloudflare"}:
        return "partial"
    return "stub"


def resolve_skill_for_provider(provider: str):
    skill = get_provider_skill(provider)
    if skill is None:
        return None, f"No provider skill registered for `{provider}`."
    return skill, None

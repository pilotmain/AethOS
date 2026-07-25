# SPDX-License-Identifier: Apache-2.0
"""Mission Control provider catalog for agent-runtime cloud tools."""

from __future__ import annotations

import re
from functools import lru_cache

# Deep agent tools (inventory, health, logs) — dedicated executors.
FIRST_CLASS_AGENT_PROVIDERS: frozenset[str] = frozenset({"railway", "vercel"})

# Provider skills with discover() beyond generic token validation.
SKILL_BACKED_PROVIDERS: frozenset[str] = frozenset(
    {"github", "aws", "gcp", "azure", "cloudflare", "kubernetes", "docker", "k8s"}
)


@lru_cache(maxsize=1)
def list_mission_control_providers() -> tuple[str, ...]:
    from aethos_core.providers.base.provider_registry import ProviderRegistry

    return tuple(ProviderRegistry.list_names())


def list_agent_cloud_providers() -> list[str]:
    """All providers registered in Mission Control Provider Inventory."""
    return list(list_mission_control_providers())


def provider_display_name(provider: str) -> str:
    from aethos_core.providers.base.provider_registry import ProviderRegistry

    spec = ProviderRegistry.get(provider)
    if spec and spec.label:
        return spec.label
    return (provider or "unknown").replace("_", " ").title()


def is_registered_provider(provider: str) -> bool:
    key = (provider or "").strip().lower()
    return key in list_mission_control_providers()


def normalize_provider_name(provider: str) -> str | None:
    key = (provider or "").strip().lower()
    if key == "k8s":
        key = "kubernetes"
    if not key or not is_registered_provider(key):
        return None
    return key


def build_provider_name_pattern() -> re.Pattern[str]:
    names = sorted(set(list_mission_control_providers()), key=len, reverse=True)
    alts: list[str] = []
    for name in names:
        alts.append(re.escape(name))
        spaced = name.replace("_", " ")
        if spaced != name:
            alts.append(re.escape(spaced))
    if not alts:
        alts = ["vercel", "railway", "github"]
    return re.compile(rf"\b({'|'.join(alts)})\b", re.I)

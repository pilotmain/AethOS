# SPDX-License-Identifier: Apache-2.0
"""Provider acceleration — provider degradation momentum."""

from __future__ import annotations

from typing import Any

from aethos_core.runtime_fragility.provider_fragility import detect_provider_fragility


def detect_provider_acceleration(*, provider: str = "railway") -> dict[str, Any]:
    provider_f = detect_provider_fragility(provider=provider)
    return {
        **provider_f,
        "accelerating": provider_f.get("fragility_elevated", False),
        "summary": f"Provider degradation momentum monitored for {provider}.",
    }

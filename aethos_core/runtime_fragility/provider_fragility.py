# SPDX-License-Identifier: Apache-2.0
"""Provider fragility — provider degradation tendencies."""

from __future__ import annotations

from typing import Any

from aethos_core.infrastructure_fragility.provider_fragility import assess_provider_fragility


def detect_provider_fragility(*, provider: str = "railway") -> dict[str, Any]:
    return assess_provider_fragility(provider=provider)

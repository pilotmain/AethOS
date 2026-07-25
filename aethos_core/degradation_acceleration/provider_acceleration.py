# SPDX-License-Identifier: Apache-2.0
"""Provider acceleration — provider degradation growth."""

from __future__ import annotations

from typing import Any

from aethos_core.fragility_acceleration.provider_acceleration import detect_provider_acceleration


def measure_provider_acceleration(*, provider: str = "railway") -> dict[str, Any]:
    return detect_provider_acceleration(provider=provider)

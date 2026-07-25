# SPDX-License-Identifier: Apache-2.0
"""Provider instability memory — provider degradation."""

from __future__ import annotations

from typing import Any

from aethos_core.long_tail_resilience_memory.provider_instability_memory import recall_provider_instability


def recall_provider_degradation(*, provider: str = "railway") -> dict[str, Any]:
    return recall_provider_instability(provider=provider)

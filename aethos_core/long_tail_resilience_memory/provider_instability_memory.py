# SPDX-License-Identifier: Apache-2.0
"""Provider instability memory — provider degradation."""

from __future__ import annotations

from typing import Any

from aethos_core.long_tail_operational_memory.provider_operational_memory import recall_provider_operational_memory


def recall_provider_instability(*, provider: str = "railway") -> dict[str, Any]:
    return recall_provider_operational_memory(provider=provider)

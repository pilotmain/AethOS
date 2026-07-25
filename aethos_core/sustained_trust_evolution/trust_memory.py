# SPDX-License-Identifier: Apache-2.0
"""Trust memory — trust trajectory evolution."""

from __future__ import annotations

from typing import Any

from aethos_core.temporal_trust_evolution.long_tail_trust_memory import record_long_tail_trust


def record_trust_memory(*, score: float = 0.89) -> dict[str, Any]:
    return record_long_tail_trust(score=score)

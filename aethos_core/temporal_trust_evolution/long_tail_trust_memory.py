# SPDX-License-Identifier: Apache-2.0
"""Long tail trust memory — trust trajectory history."""

from __future__ import annotations

from typing import Any

from aethos_core.temporal_confidence.temporal_trust_memory import record_trust_evolution


def record_long_tail_trust(*, score: float = 0.88) -> dict[str, Any]:
    return record_trust_evolution(score=score)

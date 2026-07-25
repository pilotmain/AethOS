# SPDX-License-Identifier: Apache-2.0
"""Resilience exhaustion intelligence aggregate."""

from __future__ import annotations

from typing import Any

from aethos_core.resilience_exhaustion_intelligence.exhaustion_runtime import orchestrate_resilience_exhaustion_intelligence


def assess_resilience_exhaustion_intelligence() -> dict[str, Any]:
    exhaustion = orchestrate_resilience_exhaustion_intelligence()
    return {"ok": True, **exhaustion}

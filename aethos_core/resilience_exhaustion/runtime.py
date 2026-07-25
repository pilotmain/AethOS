# SPDX-License-Identifier: Apache-2.0
"""Resilience exhaustion aggregate."""

from __future__ import annotations

from typing import Any

from aethos_core.resilience_exhaustion.exhaustion_runtime import orchestrate_resilience_exhaustion


def assess_resilience_exhaustion() -> dict[str, Any]:
    exhaustion = orchestrate_resilience_exhaustion()
    return {"ok": True, **exhaustion}

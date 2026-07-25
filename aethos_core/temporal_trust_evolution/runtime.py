# SPDX-License-Identifier: Apache-2.0
"""Temporal trust evolution aggregate."""

from __future__ import annotations

from typing import Any

from aethos_core.temporal_trust_evolution.trust_evolution_runtime import orchestrate_trust_evolution


def assess_temporal_trust_evolution() -> dict[str, Any]:
    trust = orchestrate_trust_evolution()
    return {"ok": True, **trust}

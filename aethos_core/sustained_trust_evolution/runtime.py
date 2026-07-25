# SPDX-License-Identifier: Apache-2.0
"""Sustained trust evolution aggregate."""

from __future__ import annotations

from typing import Any

from aethos_core.sustained_trust_evolution.trust_runtime import orchestrate_sustained_trust


def assess_sustained_trust_evolution() -> dict[str, Any]:
    trust = orchestrate_sustained_trust()
    return {"ok": True, **trust}

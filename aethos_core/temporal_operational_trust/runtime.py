# SPDX-License-Identifier: Apache-2.0
"""Temporal operational trust aggregate."""

from __future__ import annotations

from typing import Any

from aethos_core.temporal_operational_trust.temporal_trust_runtime import orchestrate_temporal_trust


def assess_temporal_operational_trust() -> dict[str, Any]:
    trust = orchestrate_temporal_trust()
    return {
        "ok": True,
        **trust,
        "summary": trust.get("summary", "Temporal operational trust assessing."),
    }

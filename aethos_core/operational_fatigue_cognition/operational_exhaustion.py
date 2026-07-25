# SPDX-License-Identifier: Apache-2.0
"""Operational exhaustion — runtime fatigue cognition."""

from __future__ import annotations

from typing import Any

from aethos_core.operational_fatigue_intelligence.operational_strain import assess_operational_strain


def assess_operational_exhaustion() -> dict[str, Any]:
    return assess_operational_strain()

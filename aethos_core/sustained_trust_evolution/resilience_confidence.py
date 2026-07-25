# SPDX-License-Identifier: Apache-2.0
"""Resilience confidence — resilience weighting."""

from __future__ import annotations

from typing import Any

from aethos_core.temporal_trust_evolution.resilience_confidence import assess_resilience_confidence


def assess_resilience_confidence_weighting() -> dict[str, Any]:
    return assess_resilience_confidence()

# SPDX-License-Identifier: Apache-2.0
"""Resilience decay projection — resilience erosion."""

from __future__ import annotations

from typing import Any

from aethos_core.sustained_stability_forecasting.resilience_decay_projection import project_resilience_decay


def project_resilience_erosion(*, hours: float = 10.0) -> dict[str, Any]:
    return project_resilience_decay(hours=hours)

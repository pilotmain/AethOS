# SPDX-License-Identifier: Apache-2.0
"""Long tail projection — future stability trajectories."""

from __future__ import annotations

from typing import Any

from aethos_core.sustained_stability_forecasting.long_tail_projection import project_long_tail_stability


def project_future_stability() -> dict[str, Any]:
    return project_long_tail_stability()

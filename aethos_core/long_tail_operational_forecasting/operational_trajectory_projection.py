# SPDX-License-Identifier: Apache-2.0
"""Operational trajectory projection — long-tail operational evolution."""

from __future__ import annotations

from typing import Any

from aethos_core.predictive_runtime_stability.long_tail_projection import project_future_stability


def project_operational_trajectory() -> dict[str, Any]:
    return project_future_stability()

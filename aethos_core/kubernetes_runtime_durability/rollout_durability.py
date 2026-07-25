# SPDX-License-Identifier: Apache-2.0
"""Rollout durability — rollout resilience."""

from __future__ import annotations

from typing import Any

from aethos_core.kubernetes_resilience.rollout_resilience import assess_rollout_resilience


def assess_rollout_durability() -> dict[str, Any]:
    return assess_rollout_resilience()

# SPDX-License-Identifier: Apache-2.0
"""Replay continuity projection — replay survivability."""

from __future__ import annotations

from typing import Any

from aethos_core.replay_longevity_forecasting.continuity_longevity import assess_continuity_longevity


def project_replay_continuity() -> dict[str, Any]:
    return assess_continuity_longevity()

# SPDX-License-Identifier: Apache-2.0
"""Replay projection — replay persistence durability."""

from __future__ import annotations

from typing import Any

from aethos_core.sustained_stability_forecasting.replay_durability_projection import project_replay_durability


def project_replay_persistence() -> dict[str, Any]:
    return project_replay_durability()

# SPDX-License-Identifier: Apache-2.0
"""Replay stability tracking — replay convergence."""

from __future__ import annotations

from typing import Any

from aethos_core.sustained_verification.replay_stability import assess_replay_stability


def track_replay_stability() -> dict[str, Any]:
    return assess_replay_stability()

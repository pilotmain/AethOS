# SPDX-License-Identifier: Apache-2.0
"""Replay recovery tracking — replay stabilization."""

from __future__ import annotations

from typing import Any

from aethos_core.recovery_truth_convergence.replay_recovery import assess_replay_recovery


def track_replay_recovery() -> dict[str, Any]:
    return assess_replay_recovery()

# SPDX-License-Identifier: Apache-2.0
"""Replay window tracking — replay continuity."""

from __future__ import annotations

from typing import Any

from aethos_core.runtime_truth_convergence.replay_truth_alignment import align_replay_truth


def track_replay_window() -> dict[str, Any]:
    return align_replay_truth()

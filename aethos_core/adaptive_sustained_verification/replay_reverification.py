# SPDX-License-Identifier: Apache-2.0
"""Replay reverification — replay continuity."""

from __future__ import annotations

from typing import Any

from aethos_core.sustained_verification.replay_stability import assess_replay_stability


def run_replay_reverification() -> dict[str, Any]:
    return assess_replay_stability()

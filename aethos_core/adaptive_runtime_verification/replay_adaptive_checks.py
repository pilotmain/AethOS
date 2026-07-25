# SPDX-License-Identifier: Apache-2.0
"""Replay adaptive checks — replay continuity."""

from __future__ import annotations

from typing import Any

from aethos_core.adaptive_sustained_verification.replay_reverification import run_replay_reverification


def run_replay_adaptive_checks() -> dict[str, Any]:
    return run_replay_reverification()

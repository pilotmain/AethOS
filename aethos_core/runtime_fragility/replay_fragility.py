# SPDX-License-Identifier: Apache-2.0
"""Replay fragility — replay instability."""

from __future__ import annotations

from typing import Any

from aethos_core.infrastructure_fragility.replay_fragility import assess_replay_fragility


def detect_replay_fragility() -> dict[str, Any]:
    return assess_replay_fragility()

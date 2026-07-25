# SPDX-License-Identifier: Apache-2.0
"""Replay trust — replay persistence trust."""

from __future__ import annotations

from typing import Any

from aethos_core.temporal_operational_trust.replay_trust import assess_replay_trust


def assess_replay_persistence_trust() -> dict[str, Any]:
    return assess_replay_trust()

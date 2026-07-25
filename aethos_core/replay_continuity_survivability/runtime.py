# SPDX-License-Identifier: Apache-2.0
"""Replay continuity survivability aggregate."""

from __future__ import annotations

from typing import Any

from aethos_core.replay_continuity_survivability.replay_survivability_runtime import orchestrate_replay_continuity_survivability


def assess_replay_continuity_survivability() -> dict[str, Any]:
    replay = orchestrate_replay_continuity_survivability()
    return {"ok": True, **replay}

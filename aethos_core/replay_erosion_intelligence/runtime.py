# SPDX-License-Identifier: Apache-2.0
"""Replay erosion intelligence aggregate."""

from __future__ import annotations

from typing import Any

from aethos_core.replay_erosion_intelligence.replay_runtime import orchestrate_replay_erosion


def assess_replay_erosion_intelligence() -> dict[str, Any]:
    replay = orchestrate_replay_erosion()
    return {"ok": True, **replay}

# SPDX-License-Identifier: Apache-2.0
"""Replay forecast storytelling — replay narratives."""

from __future__ import annotations

from typing import Any

from aethos_core.replay_resilience.replay_story_resilience import build_replay_narrative


def tell_replay_forecast_story(*, resilient: bool = True) -> dict[str, Any]:
    return build_replay_narrative(resilient=resilient)

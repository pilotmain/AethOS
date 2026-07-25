# SPDX-License-Identifier: Apache-2.0
"""Replay resilience aggregate."""

from __future__ import annotations

from typing import Any

from aethos_core.replay_resilience.replay_runtime import orchestrate_replay_resilience


def assess_replay_resilience_cognition() -> dict[str, Any]:
    replay = orchestrate_replay_resilience()
    return {"ok": True, **replay}

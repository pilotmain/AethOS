# SPDX-License-Identifier: Apache-2.0
"""Replay resilience intelligence aggregate."""

from __future__ import annotations

from typing import Any

from aethos_core.replay_resilience_intelligence.replay_resilience_runtime import orchestrate_replay_resilience


def assess_replay_resilience_intelligence() -> dict[str, Any]:
    replay = orchestrate_replay_resilience()
    return {"ok": True, **replay}

# SPDX-License-Identifier: Apache-2.0
"""Replay persistence aggregate."""

from __future__ import annotations

from typing import Any

from aethos_core.replay_persistence.replay_persistence_runtime import orchestrate_replay_persistence


def assess_replay_persistence_intelligence() -> dict[str, Any]:
    persistence = orchestrate_replay_persistence()
    return {"ok": True, **persistence}

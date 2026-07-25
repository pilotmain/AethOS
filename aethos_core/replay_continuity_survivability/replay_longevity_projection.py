# SPDX-License-Identifier: Apache-2.0
"""Replay longevity projection — replay continuity lifespan."""

from __future__ import annotations

from typing import Any

from aethos_core.runtime_survivability_intelligence.replay_survivability_projection import project_replay_survivability


def project_replay_longevity() -> dict[str, Any]:
    return project_replay_survivability()

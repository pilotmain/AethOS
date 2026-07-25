# SPDX-License-Identifier: Apache-2.0
"""FIX 137 — job replay contract (read-only)."""

from __future__ import annotations

from typing import Final

JOB_REPLAY_SCHEMA_VERSION: Final[str] = "mission_control_job_replay_v1"
JOB_REPLAY_FIX: Final[str] = "FIX 137"
JOB_REPLAY_DEEP_LINK_FIX: Final[str] = "FIX 137B"
MUTATION_PERFORMED_FIX_137: Final[bool] = False

# Replay is derived from evidence bundle data — never triggers execution.
JOB_REPLAY_SOURCE_FIX: Final[str] = "FIX 136"

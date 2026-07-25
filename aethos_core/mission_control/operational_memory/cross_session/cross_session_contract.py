# SPDX-License-Identifier: Apache-2.0
"""FIX 140 — cross-session organizational memory contract (read-only)."""

from __future__ import annotations

from typing import Final

CROSS_SESSION_MEMORY_SCHEMA_VERSION: Final[str] = "mission_control_cross_session_memory_v1"
CROSS_SESSION_MEMORY_RECORD_SCHEMA_VERSION: Final[str] = "mission_control_operational_memory_record_v1"
CROSS_SESSION_MEMORY_FIX: Final[str] = "FIX 140"
MUTATION_PERFORMED_FIX_140: Final[bool] = False
AUTONOMOUS_ADAPTATION_ENABLED_FIX_140: Final[bool] = False
AUTONOMOUS_OPTIMIZATION_ENABLED_FIX_140: Final[bool] = False

CROSS_SESSION_MEMORY_ROUTE_ID: Final[str] = "mission_control_cross_session_memory"

CROSS_SESSION_MEMORY_INVARIANT: Final[str] = (
    "cross_session_operational_memory_is_read_only_persistence_no_autonomous_adaptation_or_execution"
)

MAX_PERSISTED_RECORDS_DEFAULT: Final[int] = 200

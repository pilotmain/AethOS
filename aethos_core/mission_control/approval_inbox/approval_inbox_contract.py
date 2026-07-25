# SPDX-License-Identifier: Apache-2.0
"""FIX 132 — Mission Control approval inbox contract (view-only)."""

from __future__ import annotations

from typing import Final

APPROVAL_INBOX_SCHEMA_VERSION: Final[str] = "mission_control_approval_inbox_v1"
APPROVAL_INBOX_FIX: Final[str] = "FIX 132"
MUTATION_PERFORMED_FIX_132: Final[bool] = False
# FIX 132 inbox was view-only; FIX 133 enables governed chat-routed approval for eligible gates only.
APPROVAL_EXECUTION_ENABLED_FIX_132: Final[bool] = False
APPROVAL_EXECUTION_ENABLED_FIX_133: Final[bool] = True

SEVERITY_ORDER: Final[tuple[str, ...]] = ("critical", "high", "medium", "low")

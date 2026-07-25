# SPDX-License-Identifier: Apache-2.0
"""Backward-compatible re-exports — prefer channels.outbound directly."""

from __future__ import annotations

from aethos_core.channels.outbound import (
    APPROVABLE_PREFLIGHT,
    clear_progress_state_for_tests,
    dispatch_job_event,
    dispatch_job_lifecycle,
)

# Tests import private helpers from dispatch module historically.
from aethos_core.channels.outbound import _condense_progress_message  # noqa: F401

__all__ = [
    "APPROVABLE_PREFLIGHT",
    "clear_progress_state_for_tests",
    "dispatch_job_event",
    "dispatch_job_lifecycle",
    "_condense_progress_message",
]

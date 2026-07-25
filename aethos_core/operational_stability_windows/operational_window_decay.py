# SPDX-License-Identifier: Apache-2.0
"""Operational window decay — delayed degradation."""

from __future__ import annotations

from typing import Any

from aethos_core.sustained_verification_windows.operational_window_decay import assess_operational_window_decay


def assess_window_decay() -> dict[str, Any]:
    return assess_operational_window_decay()

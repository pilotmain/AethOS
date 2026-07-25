# SPDX-License-Identifier: Apache-2.0
"""Operational window decay — delayed degradation."""

from __future__ import annotations

from typing import Any

from aethos_core.runtime_decay.temporal_decay import assess_temporal_decay


def assess_operational_window_decay() -> dict[str, Any]:
    return assess_temporal_decay(hours=3.0)

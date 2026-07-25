# SPDX-License-Identifier: Apache-2.0
"""Debug visibility — mode-aware exposure."""

from __future__ import annotations


def debug_allowed(*, mode: str, explicit_debug: bool = False) -> bool:
    return explicit_debug or mode in ("debug", "mission_control")

# SPDX-License-Identifier: Apache-2.0
"""Engineering visibility — operator-only detail."""

from __future__ import annotations


def is_engineering_mode(mode: str) -> bool:
    return mode in ("engineering", "operator", "debug", "mission_control")

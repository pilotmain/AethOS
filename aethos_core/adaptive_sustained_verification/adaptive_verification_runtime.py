# SPDX-License-Identifier: Apache-2.0
"""Adaptive verification runtime — dynamic verification."""

from __future__ import annotations

from typing import Any

from aethos_core.sustained_verification.verification_runtime import orchestrate_verification


def run_adaptive_verification(*, cycles_completed: int = 3) -> dict[str, Any]:
    return orchestrate_verification(cycles_completed=cycles_completed, cycles_required=4)

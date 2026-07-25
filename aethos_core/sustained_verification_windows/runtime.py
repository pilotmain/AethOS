# SPDX-License-Identifier: Apache-2.0
"""Sustained verification windows aggregate."""

from __future__ import annotations

from typing import Any

from aethos_core.sustained_verification_windows.long_tail_health import assess_long_tail_health
from aethos_core.sustained_verification_windows.operational_window_decay import assess_operational_window_decay
from aethos_core.sustained_verification_windows.recovery_window_runtime import validate_recovery_window
from aethos_core.sustained_verification_windows.replay_window_validation import validate_replay_window
from aethos_core.sustained_verification_windows.topology_window_checks import run_topology_window_checks
from aethos_core.sustained_verification_windows.verification_windows import assess_verification_windows


def assess_sustained_verification_windows() -> dict[str, Any]:
    windows = assess_verification_windows(hours_elapsed=4.5)
    long_tail = assess_long_tail_health()
    replay = validate_replay_window()
    topology = run_topology_window_checks()
    recovery = validate_recovery_window()
    decay = assess_operational_window_decay()
    qualified = windows.get("window_satisfied") and decay.get("decay_bounded", True)
    return {
        "ok": True,
        "verification_windows": windows,
        "long_tail_health": long_tail,
        "replay_window": replay,
        "topology_window": topology,
        "recovery_window": recovery,
        "window_decay": decay,
        "window_qualified": qualified,
        "summary": windows.get("summary", "Verification windows assessing."),
    }

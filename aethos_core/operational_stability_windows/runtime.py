# SPDX-License-Identifier: Apache-2.0
"""Operational stability windows aggregate."""

from __future__ import annotations

from typing import Any

from aethos_core.operational_stability_windows.operational_window_decay import assess_window_decay
from aethos_core.operational_stability_windows.replay_window_tracking import track_replay_window
from aethos_core.operational_stability_windows.stability_windows import assess_stability_windows
from aethos_core.operational_stability_windows.topology_window_runtime import run_topology_window_runtime
from aethos_core.operational_stability_windows.verification_window_memory import record_window_convergence


def assess_operational_stability_windows() -> dict[str, Any]:
    from aethos_core.operational_stability_windows.dependency_window_checks import run_dependency_window_checks

    windows = assess_stability_windows()
    replay = track_replay_window()
    dependency = run_dependency_window_checks()
    topology = run_topology_window_runtime()
    decay = assess_window_decay()
    memory = record_window_convergence(qualified=windows.get("window_satisfied", False))
    qualified = windows.get("window_satisfied") and decay.get("decay_bounded", True)
    return {
        "ok": True,
        "stability_windows": windows,
        "replay_window": replay,
        "dependency_window": dependency,
        "topology_window": topology,
        "window_decay": decay,
        "memory": memory,
        "window_qualified": qualified,
        "summary": windows.get("summary", "Operational stability windows assessing."),
    }

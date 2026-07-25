# SPDX-License-Identifier: Apache-2.0
"""Topology window runtime — topology convergence."""

from __future__ import annotations

from typing import Any

from aethos_core.runtime_truth_convergence.topology_truth_alignment import align_topology_truth


def run_topology_window_runtime() -> dict[str, Any]:
    return align_topology_truth()

# SPDX-License-Identifier: Apache-2.0
"""Topology window checks — dependency stabilization."""

from __future__ import annotations

from typing import Any

from aethos_core.runtime_reconciliation.topology_alignment import assess_topology_alignment


def run_topology_window_checks() -> dict[str, Any]:
    return assess_topology_alignment()

# SPDX-License-Identifier: Apache-2.0
"""Topology adaptive verification — dependency convergence."""

from __future__ import annotations

from typing import Any

from aethos_core.adaptive_sustained_verification.dependency_reverification import run_dependency_reverification


def run_topology_adaptive_verification() -> dict[str, Any]:
    return run_dependency_reverification()

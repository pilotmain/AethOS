# SPDX-License-Identifier: Apache-2.0
"""Dependency endurance projection — downstream survivability."""

from __future__ import annotations

from typing import Any

from aethos_core.operational_endurance.dependency_endurance import assess_dependency_endurance


def project_dependency_endurance() -> dict[str, Any]:
    return assess_dependency_endurance()

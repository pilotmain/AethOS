# SPDX-License-Identifier: Apache-2.0
"""Dependency reverification — downstream truth."""

from __future__ import annotations

from typing import Any

from aethos_core.sustained_verification.drift_reverification import assess_drift_reverification


def run_dependency_reverification() -> dict[str, Any]:
    return assess_drift_reverification()

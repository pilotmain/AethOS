# SPDX-License-Identifier: Apache-2.0
"""Execution patience — prevent premature completion."""

from __future__ import annotations

from typing import Any

from aethos_core.production_execution_truth.execution_patience import assess_execution_patience


def assess_execution_patience_intel(*, stabilization: dict[str, Any], verification: dict[str, Any]) -> dict[str, Any]:
    return assess_execution_patience(stabilization=stabilization, verification=verification)

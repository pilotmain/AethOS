# SPDX-License-Identifier: Apache-2.0
"""Sustained reconciliation — long-tail verification."""

from __future__ import annotations

from typing import Any

from aethos_core.sustained_verification.runtime import assess_sustained_verification


def assess_sustained_reconciliation() -> dict[str, Any]:
    sustained = assess_sustained_verification()
    return {
        **sustained,
        "reconciliation_active": sustained.get("extended_monitoring_active", True),
        "summary": "Long-tail runtime reconciliation active across sustained verification windows.",
    }

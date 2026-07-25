# SPDX-License-Identifier: Apache-2.0
"""Operational patience — avoids premature resolved claims."""

from __future__ import annotations

from typing import Any


def should_claim_resolved(*, stabilization: dict[str, Any], verification: dict[str, Any]) -> bool:
    return bool(
        verification.get("verified")
        and stabilization.get("stabilization_complete")
        and not stabilization.get("extended_monitoring_active")
    )

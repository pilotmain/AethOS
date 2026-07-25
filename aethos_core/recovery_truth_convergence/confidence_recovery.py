# SPDX-License-Identifier: Apache-2.0
"""Confidence recovery — bounded recovery trust."""

from __future__ import annotations

from typing import Any

from aethos_core.rollback_integrity.rollback_confidence import score_rollback_confidence


def assess_confidence_recovery() -> dict[str, Any]:
    return score_rollback_confidence()

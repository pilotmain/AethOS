# SPDX-License-Identifier: Apache-2.0
"""Infrastructure reverification — topology rechecks."""

from __future__ import annotations

from typing import Any

from aethos_core.infrastructure_truth.runtime import assess_infrastructure_truth


def run_infrastructure_reverification() -> dict[str, Any]:
    infra = assess_infrastructure_truth()
    return {
        "infrastructure": infra,
        "reverified": infra.get("ok", False),
        "summary": "Infrastructure topology reverification complete.",
    }

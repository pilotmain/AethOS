# SPDX-License-Identifier: Apache-2.0
"""Constraint validator — count/ranking enforcement."""

from __future__ import annotations

from typing import Any

from aethos_core.conversation.synthesis_pkg.intent_contracts import IntentContract


def validate_constraints(*, contract: IntentContract, items: list[dict[str, Any]]) -> dict[str, Any]:
    violations: list[str] = []
    if contract.result_count is not None and len(items) != contract.result_count:
        violations.append(f"expected {contract.result_count} results, got {len(items)}")
    if contract.ranked:
        ranks = [i.get("rank") for i in items]
        if ranks != list(range(1, len(items) + 1)):
            violations.append("ranking sequence invalid")
    return {
        "valid": not violations,
        "violations": violations,
        "item_count": len(items),
        "expected_count": contract.result_count,
    }

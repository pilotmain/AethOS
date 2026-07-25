# SPDX-License-Identifier: Apache-2.0
"""Constraint runtime — count/ranking enforcement."""

from __future__ import annotations

from typing import Any

from aethos_core.conversation.synthesis_stubs import validate_constraints
from aethos_core.conversation.intent_contracts import IntentContract
from aethos_core.conversation.synthesis_stubs import converge_ranking


def enforce_constraints(*, contract: IntentContract, items: list[dict[str, Any]]) -> dict[str, Any]:
    converged = converge_ranking(items=items, contract=contract)
    validation = validate_constraints(contract=contract, items=converged)
    return {"items": converged, "validation": validation, "enforced": validation.get("valid", False)}

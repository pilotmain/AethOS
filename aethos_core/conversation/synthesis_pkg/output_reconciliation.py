# SPDX-License-Identifier: Apache-2.0
"""Output reconciliation — final response verification."""

from __future__ import annotations

from typing import Any

from aethos_core.conversation.synthesis_pkg.constraint_validator import validate_constraints
from aethos_core.conversation.synthesis_pkg.intent_contracts import IntentContract
from aethos_core.conversation.synthesis_pkg.synthesis_guardrails import guard_output
from aethos_core.presentation_safety.premium_cleanroom import cleanroom_polish


def reconcile_output(
    *,
    reply: str,
    contract: IntentContract,
    items: list[dict[str, Any]],
    mode: str = "casual",
) -> dict[str, Any]:
    polished = cleanroom_polish(reply, mode=mode)
    constraints = validate_constraints(contract=contract, items=items)
    guard = guard_output(polished)
    verified = constraints["valid"] and guard["clean"]
    return {
        "verified": verified,
        "reply": polished,
        "constraints": constraints,
        "guardrails": guard,
    }

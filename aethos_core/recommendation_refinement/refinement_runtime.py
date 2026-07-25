# SPDX-License-Identifier: Apache-2.0
"""Recommendation refinement orchestrator."""

from __future__ import annotations

from typing import Any

from aethos_core.conversation.intent_contracts import IntentContract, parse_intent_contract
from aethos_core.conversation.synthesis_stubs import evidence_to_recommendations
from aethos_core.intent_reliability.constraint_runtime import enforce_constraints
from aethos_core.recommendation_refinement.recommendation_quality import score_recommendation_quality


def refine_recommendations(*, query: str, evidence: list[Any]) -> dict[str, Any]:
    contract = parse_intent_contract(query)
    items = evidence_to_recommendations(evidence, contract=contract)
    enforced = enforce_constraints(contract=contract, items=items)
    quality = score_recommendation_quality(enforced.get("items") or [])
    return {
        "ok": True,
        "contract": contract.to_dict(),
        "items": enforced.get("items") or [],
        "enforcement": enforced,
        "quality": quality,
        "summary": quality.get("summary", ""),
    }

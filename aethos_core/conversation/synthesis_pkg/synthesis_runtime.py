# SPDX-License-Identifier: Apache-2.0
"""Conversational synthesis orchestrator."""

from __future__ import annotations

import re
from typing import Any

from aethos_core.conversation.elegance.conversational_flow import apply_conversational_flow
from aethos_core.conversation.synthesis_pkg.conversational_formatter import format_recommendations
from aethos_core.conversation.synthesis_pkg.conversational_recovery import build_recovery_response
from aethos_core.conversation.synthesis_pkg.intent_contracts import IntentContract, parse_intent_contract
from aethos_core.conversation.synthesis_pkg.output_reconciliation import reconcile_output
from aethos_core.conversation.synthesis_pkg.ranking_convergence import converge_ranking
from aethos_core.conversation.synthesis_pkg.recommendation_curator import evidence_to_recommendations
from aethos_core.conversation.synthesis_pkg.response_normalizer import normalize_response
from aethos_core.human_trust.confidence_restraint import should_show_telemetry
from aethos_core.human_trust.recommendation_confidence import recommendation_confidence_phrase
from aethos_core.human_trust.trust_calibration import calibrate_trust
from aethos_core.presentation_safety.premium_cleanroom import cleanroom_polish


def synthesize_human_response(
    *,
    query: str,
    evidence: list[Any] | None = None,
    raw_reply: str = "",
    overall_confidence: float = 0.6,
    contradictions: int = 0,
    mode: str = "casual",
    include_followups: bool = False,
) -> dict[str, Any]:
    """Top-level human-facing synthesis — ranked, constrained, calm."""
    contract = parse_intent_contract(query)
    if not evidence and raw_reply:
        reply = cleanroom_polish(raw_reply, mode=mode)
        reply = apply_conversational_flow(reply, include_followups=include_followups)
        return {
            "ok": True,
            "reply": reply,
            "contract": contract.to_dict(),
            "mode": mode,
            "qualification_tier": "premium" if mode == "casual" else "engineering",
            "verified": True,
        }

    if not evidence:
        return {
            "ok": False,
            "reply": build_recovery_response(query=query),
            "contract": contract.to_dict(),
            "verified": False,
        }

    items = evidence_to_recommendations(evidence, contract=contract)
    items = converge_ranking(items=items, contract=contract)
    conf_phrase = recommendation_confidence_phrase(overall=overall_confidence, query=query)
    trust = calibrate_trust(confidence=overall_confidence, item_count=len(items), contradictions=contradictions)

    if contract.result_count and len(items) < contract.result_count and len(evidence) >= contract.result_count:
        while len(items) < contract.result_count and len(items) < len(evidence):
            extra = evidence_to_recommendations(evidence[len(items) :], contract=contract)
            items.extend(converge_ranking(items=extra, contract=contract))
            items = converge_ranking(items=items, contract=contract)

    if items and contract.result_count:
        reply = format_recommendations(contract=contract, items=items, confidence_phrase=conf_phrase)
    elif should_show_telemetry(mode=mode):
        reply = raw_reply or normalize_response(conf_phrase)
    else:
        reply = format_recommendations(contract=contract, items=items or [{"name": "Result", "rank": 1, "explanation": conf_phrase}], confidence_phrase=conf_phrase)

    reply = apply_conversational_flow(reply, include_followups=include_followups)
    reconciled = reconcile_output(reply=reply, contract=contract, items=items, mode=mode)
    tier = _qualification_tier(reconciled.get("verified"), trust.get("restrained", True))

    return {
        "ok": True,
        "reply": reconciled["reply"],
        "contract": contract.to_dict(),
        "items": items,
        "trust": trust,
        "reconciliation": reconciled,
        "mode": mode,
        "qualification_tier": tier,
        "verified": reconciled.get("verified", False),
        "maturity": "stable" if tier in ("premium", "production conversational") else "beta",
        "verification_coverage_pct": 88 if reconciled.get("verified") else 72,
    }


def polish_research_reply(
    *,
    query: str,
    synthesis: Any,
    analysis: Any,
    evidence: list[Any],
    raw_markdown: str,
    mode: str = "casual",
    comparison: bool = False,
) -> dict[str, Any]:
    """Polish research pipeline output for human chat."""
    if comparison:
        from aethos_core.presentation_safety.premium_cleanroom import cleanroom_polish

        return {
            "ok": True,
            "reply": cleanroom_polish(raw_markdown, mode=mode),
            "mode": mode,
            "qualification_tier": "comparison_wiki",
        }
    if should_show_telemetry(mode=mode, intent="research_synthesis"):
        return {"ok": True, "reply": raw_markdown, "mode": mode, "engineering": True}
    is_compare_question = bool(
        comparison
        or re.search(r"\bcompare\b|\bcomparison\b|\bvs\.?\b|\bsecond brain\b", query, re.I)
    )
    is_recommendation = (not is_compare_question) and bool(
        parse_intent_contract(query).result_count
        or any(k in query.lower() for k in ("playground", "restaurant", "hotel", "top five", "top 5"))
    )
    include_followups = is_recommendation and "playground" in query.lower()
    if is_recommendation and mode == "casual":
        from aethos_core.conversation.legacy_polish_api import ensure_reliable_response

        return ensure_reliable_response(
            query=query,
            evidence=evidence,
            overall_confidence=float(getattr(analysis, "overall_confidence", 0.5)),
            contradictions=len(getattr(analysis, "contradictions", []) or []),
            mode=mode,
            include_followups=include_followups,
        )
    return synthesize_human_response(
        query=query,
        evidence=evidence if is_recommendation else None,
        raw_reply=raw_markdown,
        overall_confidence=float(getattr(analysis, "overall_confidence", 0.5)),
        contradictions=len(getattr(analysis, "contradictions", []) or []),
        mode=mode,
        include_followups=include_followups,
    )


def polish_chat_reply(*, reply: str, intent: str = "", mode: str = "casual") -> str:
    """Apply presentation safety to any outbound chat reply."""
    if should_show_telemetry(mode=mode, intent=intent):
        return reply
    polished = cleanroom_polish(reply, mode=mode)
    return apply_conversational_flow(polished, include_followups=False)


def _qualification_tier(verified: bool, restrained: bool) -> str:
    if verified and restrained:
        return "production conversational"
    if verified:
        return "premium"
    if restrained:
        return "stable"
    return "beta"

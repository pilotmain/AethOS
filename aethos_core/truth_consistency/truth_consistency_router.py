# SPDX-License-Identifier: Apache-2.0
"""FIX 316C — truth consistency chat router."""

from __future__ import annotations

from aethos_core.truth_consistency.truth_consistency_contract import TRUTH_CONSISTENCY_ROUTE_ID
from aethos_core.truth_consistency.truth_consistency_intent import (
    handle_truth_consistency_intent,
    parse_truth_consistency_intent,
)
from aethos_core.truth_consistency.truth_consistency_renderer import render_truth_consistency_markdown
from aethos_core.truth_consistency.truth_consistency_service import build_truth_consistency


def _meta(*, session_id: str, intent: str) -> dict[str, str]:
    return {
        "route_id": TRUTH_CONSISTENCY_ROUTE_ID,
        "matched_module": "truth_consistency.truth_consistency_router",
        "session_id": session_id,
        "intent": intent,
        "suppress_governance_footer": "true",
        "show_governance_footer": "false",
        "presentation_mode": "casual",
        "lane": "truth_consistency",
        "truth_consistency_layer": "true",
    }


def route_truth_consistency(
    text: str,
    *,
    session_id: str = "default",
) -> tuple[str, str, dict[str, str]] | None:
    parsed = parse_truth_consistency_intent(text)
    if parsed is None:
        return None

    sid = (session_id or "default").strip()[:64] or "default"

    if parsed.get("action") == "record":
        handle_truth_consistency_intent(parsed, session_id=sid)
        return (
            "Truth review recorded. This command is record-only and does not rewrite answers or mutate platform truth.",
            "truth_review_record",
            _meta(session_id=sid, intent="truth_review_record"),
        )

    if parsed.get("action") == "view":
        payload = build_truth_consistency(session_id=sid).truth_consistency
        body = render_truth_consistency_markdown(payload=payload, focus="truth_dashboard")
        return body, "truth_dashboard", _meta(session_id=sid, intent="truth_dashboard")

    return None


def attach_truth_validation_meta(
    *,
    question: str,
    answer: str,
    session_id: str,
    response_kind: str,
    meta: dict[str, str],
) -> dict[str, str]:
    from aethos_core.truth_consistency.truth_consistency_public_answer_validator import validate_public_answer

    validation = validate_public_answer(
        question=question,
        answer=answer,
        session_id=session_id,
        response_kind=response_kind,
        lightweight=True,
    )
    enriched = dict(meta)
    enriched["truth_consistency_layer"] = "true"
    enriched["truth_validated"] = "true" if validation.get("valid") else "false"
    enriched["hallucination_detected"] = (
        "true" if validation.get("hallucination_detection_report", {}).get("hallucination_detected") else "false"
    )
    enriched["platform_truth_source"] = "certified_evidence"
    return enriched

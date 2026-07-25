# SPDX-License-Identifier: Apache-2.0
"""FIX 319 — customer feedback intelligence evaluators."""

from __future__ import annotations

import re
from collections import Counter
from typing import Any

from aethos_core.mission_control.customer_feedback_intelligence.customer_feedback_intelligence_contract import (
    FEEDBACK_CLASSIFICATIONS,
    FEEDBACK_CORE_PRINCIPLE,
    FEEDBACK_SOURCES,
    PRIVACY_REQUIREMENTS,
    SENTIMENT_LABELS,
)
from aethos_core.mission_control.customer_feedback_intelligence.customer_feedback_intelligence_evidence import (
    _section_block,
)

_POSITIVE_RX = re.compile(r"\b(great|love|helpful|clear|easy|excellent|thank)\b", re.I)
_NEGATIVE_RX = re.compile(r"\b(confus|hard|difficult|blocked|frustrat|unclear|broken|slow|trust)\b", re.I)


def _normalize_item(
    *,
    text: str,
    source: str,
    item_id: str,
    metadata: dict[str, Any] | None = None,
) -> dict[str, Any]:
    return {
        "feedback_id": item_id,
        "text": (text or "").strip(),
        "source": source,
        "tenant_scoped": True,
        "metadata": metadata or {},
    }


def _extract_feedback_items(*, evidence: dict[str, Any]) -> list[dict[str, Any]]:
    items: list[dict[str, Any]] = []

    support = evidence.get("fix_310") or {}
    for idx, row in enumerate(_section_block(support, "support_request_registry").get("requests") or []):
        if isinstance(row, dict):
            text = str(row.get("summary") or row.get("detail") or row.get("content") or "")
        else:
            text = str(row)
        if text:
            items.append(_normalize_item(text=text, source="support_notes", item_id=f"support-{idx + 1}"))

    for idx, row in enumerate(_section_block(support, "customer_success_dashboard").get("observations") or []):
        text = str(row)
        if text:
            items.append(
                _normalize_item(text=text, source="customer_success_observations", item_id=f"success-{idx + 1}")
            )

    beta = evidence.get("fix_312") or {}
    beta_feedback = _section_block(beta, "beta_feedback_registry")
    for idx, row in enumerate(beta_feedback.get("feedback_items") or []):
        if isinstance(row, dict):
            text = str(row.get("summary") or row.get("detail") or row.get("content") or row)
        else:
            text = str(row)
        if text:
            items.append(_normalize_item(text=text, source="beta_feedback", item_id=f"beta-{idx + 1}"))

    onboarding = evidence.get("fix_301") or {}
    progress = _section_block(onboarding, "onboarding_progress_registry")
    for idx, step in enumerate(progress.get("incomplete_steps") or progress.get("pending_steps") or []):
        items.append(
            _normalize_item(
                text=f"Onboarding friction at step: {step}",
                source="onboarding_feedback",
                item_id=f"onboarding-{idx + 1}",
            )
        )

    product = evidence.get("fix_311") or {}
    for idx, row in enumerate(_section_block(product, "public_product_dashboard").get("feedback_items") or []):
        text = str(row)
        if text:
            items.append(_normalize_item(text=text, source="product_feedback", item_id=f"product-{idx + 1}"))

    for idx, record in enumerate(evidence.get("feedback_review_records") or []):
        if str(record.get("kind") or "").endswith("note") or "note" in str(record.get("kind") or ""):
            items.append(
                _normalize_item(
                    text=str(record.get("content") or ""),
                    source="operator_observations",
                    item_id=f"operator-{idx + 1}",
                )
            )

    for idx, record in enumerate(evidence.get("improvement_review_records") or []):
        if "note" in str(record.get("kind") or ""):
            items.append(
                _normalize_item(
                    text=str(record.get("content") or ""),
                    source="operator_observations",
                    item_id=f"improvement-note-{idx + 1}",
                )
            )

    if not items:
        items.append(
            _normalize_item(
                text="Submitted feedback evidence pending — registry ready for tenant-scoped intake.",
                source="operator_observations",
                item_id="placeholder-1",
            )
        )

    return items


def _classify_feedback(text: str) -> str:
    lowered = (text or "").lower()
    if any(word in lowered for word in ("thank", "great", "love", "helpful", "excellent")):
        return "positive_feedback"
    if any(word in lowered for word in ("onboard", "setup", "activation", "getting started")):
        return "onboarding_issue"
    if any(word in lowered for word in ("trust", "approval", "governance", "authority")):
        return "trust_concern"
    if any(word in lowered for word in ("plan", "billing", "upgrade", "entitlement", "price")):
        return "commercial_concern"
    if any(word in lowered for word in ("deploy", "rollback", "incident", "monitor", "ops")):
        return "operational_issue"
    if any(word in lowered for word in ("confus", "unclear", "hard to", "navigation", "ui", "ux")):
        return "usability_issue"
    if any(word in lowered for word in ("capability", "feature", "can't", "cannot", "missing", "need")):
        return "capability_gap"
    if any(word in lowered for word in ("request", "want", "would like", "add")):
        return "feature_request"
    return "usability_issue"


def _sentiment_for_text(text: str) -> str:
    if _POSITIVE_RX.search(text or ""):
        return "positive"
    if _NEGATIVE_RX.search(text or ""):
        return "negative"
    return "neutral"


def build_customer_feedback_registry(*, evidence: dict[str, Any]) -> dict[str, Any]:
    items = _extract_feedback_items(evidence=evidence)
    return {
        "items": items,
        "count": len(items),
        "sources": list(FEEDBACK_SOURCES),
        "tenant_scoped": True,
        "cross_tenant_aggregation_forbidden": True,
        "validated": bool(items),
    }


def build_feedback_classification_report(*, items: list[dict[str, Any]]) -> dict[str, Any]:
    classified: list[dict[str, Any]] = []
    counts = Counter()
    for item in items:
        category = _classify_feedback(str(item.get("text") or ""))
        counts[category] += 1
        classified.append({**item, "classification": category})

    return {
        "classifications": list(FEEDBACK_CLASSIFICATIONS),
        "items": classified,
        "counts_by_classification": dict(counts),
        "validated": bool(classified),
    }


def build_feedback_sentiment_report(*, items: list[dict[str, Any]]) -> dict[str, Any]:
    sentiments: list[dict[str, Any]] = []
    counts = Counter()
    for item in items:
        sentiment = _sentiment_for_text(str(item.get("text") or ""))
        counts[sentiment] += 1
        sentiments.append({**item, "sentiment": sentiment})

    return {
        "sentiment_labels": list(SENTIMENT_LABELS),
        "items": sentiments,
        "counts_by_sentiment": dict(counts),
        "validated": bool(sentiments),
    }


def build_feedback_trend_report(*, classified_items: list[dict[str, Any]]) -> dict[str, Any]:
    theme_counter: Counter[str] = Counter()
    complaint_counter: Counter[str] = Counter()
    request_counter: Counter[str] = Counter()

    for item in classified_items:
        text = str(item.get("text") or "")
        classification = str(item.get("classification") or "")
        theme_key = classification or "general"
        theme_counter[theme_key] += 1
        if classification in {"usability_issue", "onboarding_issue", "trust_concern", "operational_issue"}:
            complaint_counter[text[:80]] += 1
        if classification in {"feature_request", "capability_gap"}:
            request_counter[text[:80]] += 1

    recurring_requests = [text for text, count in request_counter.most_common(5) if count >= 1]
    recurring_complaints = [text for text, count in complaint_counter.most_common(5) if count >= 1]
    emerging_themes = [theme for theme, _count in theme_counter.most_common(5)]

    return {
        "recurring_requests": recurring_requests,
        "recurring_complaints": recurring_complaints,
        "emerging_themes": emerging_themes,
        "theme_counts": dict(theme_counter),
        "validated": bool(theme_counter),
    }


def build_capability_gap_report(*, evidence: dict[str, Any], classified_items: list[dict[str, Any]]) -> dict[str, Any]:
    cap295 = evidence.get("fix_295") or {}
    cap296 = evidence.get("fix_296") or {}
    improvement = evidence.get("fix_317") or {}
    registry = _section_block(cap295, "capability_registry")
    existing = list(_section_block(cap296, "proven_capabilities").get("items") or [])
    existing.extend(_section_block(cap296, "operational_capabilities").get("items") or [])

    requested: list[str] = []
    gaps: list[dict[str, Any]] = []
    for item in classified_items:
        if item.get("classification") not in {"feature_request", "capability_gap"}:
            continue
        text = str(item.get("text") or "")
        requested.append(text)
        matched = any(token.lower() in " ".join(existing).lower() for token in text.split()[:4] if len(token) > 4)
        if not matched:
            gaps.append(
                {
                    "requested_capability": text[:120],
                    "existing_match": False,
                    "source": item.get("source"),
                }
            )

    improvement_ops = (
        (improvement.get("sections") or {}).get("improvement_opportunity_registry") or [{}]
    )[0].get("opportunities") or []

    return {
        "sources": ["FIX 295", "FIX 296", "FIX 317"],
        "existing_capabilities": existing[:12],
        "requested_capabilities": requested[:12],
        "gaps": gaps,
        "improvement_opportunities_linked": len(improvement_ops),
        "validated": bool(existing or requested),
    }


def build_customer_friction_report(*, evidence: dict[str, Any]) -> dict[str, Any]:
    onboarding = evidence.get("fix_301") or {}
    provider = evidence.get("fix_303") or {}
    analytics = evidence.get("fix_318") or {}
    onboarding_report = (analytics.get("sections") or {}).get("onboarding_analytics_report") or [{}]
    onboarding_report = onboarding_report[0] if onboarding_report else {}
    provider_report = (analytics.get("sections") or {}).get("provider_analytics_report") or [{}]
    provider_report = provider_report[0] if provider_report else {}
    progress = _section_block(onboarding, "onboarding_progress_registry")

    onboarding_friction = list(
        onboarding_report.get("drop_off_points")
        or progress.get("incomplete_steps")
        or progress.get("pending_steps")
        or []
    )
    provider_friction = list(provider_report.get("readiness_failures") or [])
    adoption_friction = list(
        (analytics.get("sections") or {}).get("behavioral_opportunity_registry") or [{}]
    )[0].get("opportunities") or []

    return {
        "sources": ["FIX 301", "FIX 303", "FIX 318"],
        "onboarding_friction": onboarding_friction[:8],
        "provider_friction": provider_friction[:8],
        "adoption_friction": [
            opp.get("detail") for opp in adoption_friction if isinstance(opp, dict) and opp.get("detail")
        ][:8],
        "provider_dashboard": _section_block(provider, "provider_connection_dashboard"),
        "validated": bool(onboarding_friction or provider_friction or adoption_friction),
    }


def _impact_from_classification(classification: str) -> str:
    if classification in {"trust_concern", "operational_issue", "onboarding_issue"}:
        return "high"
    if classification in {"capability_gap", "commercial_concern"}:
        return "medium"
    return "low"


def build_feedback_opportunity_registry(
    *,
    classified_items: list[dict[str, Any]],
    trend_report: dict[str, Any],
    capability_gap_report: dict[str, Any],
    friction_report: dict[str, Any],
) -> dict[str, Any]:
    opportunities: list[dict[str, Any]] = []
    theme_counts = trend_report.get("theme_counts") or {}

    for item in classified_items:
        classification = str(item.get("classification") or "usability_issue")
        if classification == "positive_feedback":
            continue
        opportunities.append(
            {
                "opportunity_id": f"feedback-{item.get('feedback_id')}",
                "title": str(item.get("text") or "")[:120],
                "classification": classification,
                "impact": _impact_from_classification(classification),
                "frequency": int(theme_counts.get(classification, 1)),
                "confidence": 0.8 if classification in theme_counts else 0.6,
                "source": item.get("source"),
                "affected_capability": classification if classification == "capability_gap" else None,
                "automatic_work_creation_forbidden": True,
            }
        )

    for gap in capability_gap_report.get("gaps") or []:
        opportunities.append(
            {
                "opportunity_id": f"cap-gap-{len(opportunities) + 1}",
                "title": str(gap.get("requested_capability") or "Capability gap"),
                "classification": "capability_gap",
                "impact": "high",
                "frequency": 1,
                "confidence": 0.85,
                "source": gap.get("source"),
                "affected_capability": gap.get("requested_capability"),
                "automatic_work_creation_forbidden": True,
            }
        )

    for point in friction_report.get("onboarding_friction") or []:
        opportunities.append(
            {
                "opportunity_id": f"friction-onboarding-{len(opportunities) + 1}",
                "title": f"Onboarding friction: {point}",
                "classification": "onboarding_issue",
                "impact": "high",
                "frequency": 1,
                "confidence": 0.82,
                "source": "onboarding_feedback",
                "affected_capability": "onboarding",
                "automatic_work_creation_forbidden": True,
            }
        )

    return {
        "opportunities": opportunities,
        "count": len(opportunities),
        "core_principle": FEEDBACK_CORE_PRINCIPLE,
    }


def _priority_score(opportunity: dict[str, Any]) -> float:
    impact_scores = {"high": 3.0, "medium": 2.0, "low": 1.0}
    impact = impact_scores.get(str(opportunity.get("impact") or "medium"), 2.0)
    frequency = float(opportunity.get("frequency") or 1)
    confidence = float(opportunity.get("confidence") or 0.5)
    strategic = 0.5 if opportunity.get("classification") in {"trust_concern", "capability_gap"} else 0.0
    effort_penalty = 0.0
    return round(impact * 2.0 + min(frequency, 5) + confidence + strategic - effort_penalty, 3)


def build_feedback_priority_matrix(*, registry: dict[str, Any]) -> dict[str, Any]:
    ranked = [{**opp, "priority_score": _priority_score(opp)} for opp in registry.get("opportunities") or []]
    ranked.sort(key=lambda row: row["priority_score"], reverse=True)
    return {
        "ranked_opportunities": ranked[:12],
        "high_frequency_high_impact": [
            row for row in ranked if row.get("impact") == "high" and int(row.get("frequency") or 0) >= 2
        ][:6],
        "strategic_considerations": ranked[:5],
        "automatic_work_creation_forbidden": True,
    }

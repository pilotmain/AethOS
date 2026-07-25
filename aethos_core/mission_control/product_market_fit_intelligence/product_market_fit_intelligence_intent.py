# SPDX-License-Identifier: Apache-2.0
"""FIX 322 — product-market fit intelligence intent."""

from __future__ import annotations

import re
from typing import Any

from aethos_core.mission_control.product_market_fit_intelligence.product_market_fit_intelligence_contract import (
    PMF_REVIEW_RECORD_KINDS,
)
from aethos_core.mission_control.product_market_fit_intelligence.product_market_fit_intelligence_store import (
    append_pmf_review_record,
)

_VIEW_DASHBOARD_RX = re.compile(
    r"^\s*show\s+(?:product[- ]market[- ]fit|pmf)(?:\s+dashboard|\s+intelligence)?\s*$",
    re.IGNORECASE,
)
_NOTE_RX = re.compile(r"^\s*pmf\s+note\s*:\s*(.+)$", re.IGNORECASE)
_DECISION_RX = re.compile(
    r"^\s*pmf\s+review\s+(?P<decision>approve|hold|reject|defer)\s*:\s*(?P<body>.+)$",
    re.IGNORECASE | re.S,
)
_VALUE_RX = re.compile(r"\bare customers finding value\b", re.I)
_CREATES_VALUE_RX = re.compile(r"\bwhich capabilities create value\b", re.I)
_IGNORED_RX = re.compile(r"\bwhich capabilities are ignored\b", re.I)
_RETENTION_RX = re.compile(r"\bwhat drives retention\b", re.I)
_EXPANSION_RX = re.compile(r"\bwhat drives expansion\b", re.I)
_STRENGTH_RX = re.compile(r"\bhow strong is product[- ]market fit\b", re.I)


def parse_product_market_fit_intelligence_intent(raw: str) -> dict[str, Any] | None:
    text = str(raw or "").strip()
    if not text:
        return None

    if _VIEW_DASHBOARD_RX.match(text):
        return {"action": "view", "focus": "product_market_fit_dashboard"}

    if _VALUE_RX.search(text):
        return {"action": "view", "focus": "customer_value_realization_report"}

    if _CREATES_VALUE_RX.search(text):
        return {"action": "view", "focus": "retention_value_report"}

    if _IGNORED_RX.search(text):
        return {"action": "view", "focus": "capability_demand_report"}

    if _RETENTION_RX.search(text):
        return {"action": "view", "focus": "retention_value_report"}

    if _EXPANSION_RX.search(text):
        return {"action": "view", "focus": "expansion_value_report"}

    if _STRENGTH_RX.search(text):
        return {"action": "view", "focus": "pmf_scorecard"}

    decision_match = _DECISION_RX.match(text)
    if decision_match:
        decision = decision_match.group("decision").lower()
        body = (decision_match.group("body") or "").strip()
        if not body:
            return None
        return {
            "action": "record",
            "kind": f"pmf_review_decision_{decision}",
            "content": body,
        }

    note_match = _NOTE_RX.match(text)
    if note_match:
        return {
            "action": "record",
            "kind": "pmf_note",
            "content": note_match.group(1).strip(),
        }

    return None


def handle_product_market_fit_intelligence_intent(
    intent: dict[str, Any],
    *,
    session_id: str = "default",
) -> dict[str, Any]:
    if intent.get("action") == "record":
        kind = str(intent["kind"])
        if kind not in PMF_REVIEW_RECORD_KINDS:
            raise ValueError(f"unsupported pmf review kind: {kind}")
        record = append_pmf_review_record(
            kind=kind,
            content=str(intent["content"]),
            session_id=session_id,
            domain=str(intent.get("domain") or "") or None,
        )
        return {"action": "record", "record": record}
    return {"action": "view", "focus": str(intent.get("focus") or "product_market_fit_dashboard")}

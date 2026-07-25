# SPDX-License-Identifier: Apache-2.0
"""FIX 311 — public product experience intent."""

from __future__ import annotations

import re
from typing import Any

from aethos_core.mission_control.public_product_experience.public_product_experience_contract import (
    PUBLIC_PRODUCT_EXPERIENCE_RECORD_KINDS,
)
from aethos_core.mission_control.public_product_experience.public_product_experience_store import (
    append_public_product_experience_record,
)

_VIEW_PRODUCT_RX = re.compile(r"^\s*show\s+public\s+product\s+experience\s*$", re.IGNORECASE)
_VIEW_CAPABILITY_RX = re.compile(r"^\s*show\s+capability\s+explorer\s*$", re.IGNORECASE)
_VIEW_TRUST_RX = re.compile(r"^\s*show\s+trust\s+explorer\s*$", re.IGNORECASE)
_VIEW_TOUR_RX = re.compile(r"^\s*show\s+guided\s+product\s+tour\s*$", re.IGNORECASE)
_VIEW_JOURNEY_RX = re.compile(r"^\s*show\s+customer\s+journey\s*$", re.IGNORECASE)
_VIEW_DASHBOARD_RX = re.compile(r"^\s*show\s+public\s+dashboard\s*$", re.IGNORECASE)

_NOTE_RX = re.compile(r"^\s*public\s+experience\s+note\s*:\s*(.+)$", re.IGNORECASE)
_DECISION_RX = re.compile(
    r"^\s*public\s+experience\s+review\s+(?P<decision>approve|hold|reject|defer)\s*:\s*(?P<body>.+)$",
    re.IGNORECASE | re.S,
)


def parse_public_product_experience_intent(raw: str) -> dict[str, Any] | None:
    text = str(raw or "").strip()
    if not text:
        return None

    if _VIEW_CAPABILITY_RX.match(text):
        return {"action": "view", "focus": "capability_explorer"}
    if _VIEW_TRUST_RX.match(text):
        return {"action": "view", "focus": "trust_explorer"}
    if _VIEW_TOUR_RX.match(text):
        return {"action": "view", "focus": "guided_product_tour"}
    if _VIEW_JOURNEY_RX.match(text):
        return {"action": "view", "focus": "customer_journey_explorer"}
    if _VIEW_DASHBOARD_RX.match(text):
        return {"action": "view", "focus": "public_product_dashboard"}
    if _VIEW_PRODUCT_RX.match(text):
        return {"action": "view", "focus": "public_product_dashboard"}

    decision_match = _DECISION_RX.match(text)
    if decision_match:
        decision = decision_match.group("decision").lower()
        body = (decision_match.group("body") or "").strip()
        if not body:
            return None
        return {
            "action": "record",
            "kind": f"public_experience_review_decision_{decision}",
            "content": body,
        }

    note_match = _NOTE_RX.match(text)
    if note_match:
        return {
            "action": "record",
            "kind": "public_experience_note",
            "content": note_match.group(1).strip(),
        }

    lowered = text.lower()
    if lowered.startswith("public experience:") or lowered.startswith("public product:"):
        body = text.split(":", 1)[1].strip()
        return {
            "action": "record",
            "kind": "public_product_experience_record",
            "content": body,
        }

    return None


def handle_public_product_experience_intent(
    intent: dict[str, Any],
    *,
    session_id: str | None = None,
) -> dict[str, Any]:
    action = intent.get("action")
    if action == "view":
        return {"action": "view", "focus": intent.get("focus") or "public_product_dashboard"}

    if action == "record":
        kind = str(intent.get("kind") or "")
        if kind not in PUBLIC_PRODUCT_EXPERIENCE_RECORD_KINDS:
            raise ValueError(f"unsupported record kind: {kind!r}")
        record = append_public_product_experience_record(
            kind=kind,
            content=str(intent.get("content") or ""),
            session_id=session_id,
            domain=str(intent.get("domain") or "") or None,
        )
        return {"action": "record", "record": record}

    raise ValueError(f"unsupported intent action: {action!r}")

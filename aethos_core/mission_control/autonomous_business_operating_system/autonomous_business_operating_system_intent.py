# SPDX-License-Identifier: Apache-2.0
"""FIX 290 — autonomous business operating system intent."""

from __future__ import annotations

import re
from typing import Any

from aethos_core.mission_control.autonomous_business_operating_system.autonomous_business_operating_system_contract import (
    AUTONOMOUS_BUSINESS_OPERATING_SYSTEM_RECORD_KINDS,
    BUSINESS_DOMAINS,
)
from aethos_core.mission_control.autonomous_business_operating_system.autonomous_business_operating_system_store import (
    append_autonomous_business_operating_system_record,
)

_VIEW_RX = re.compile(
    r"^\s*(?:show\s+)?(?:(?:autonomous\s+)?business\s+operating(?:\s+system|\s+dashboard)?|"
    r"business\s+operating\s+dashboard|"
    r"business\s+operating\s+system)\s*$",
    re.IGNORECASE,
)

_DOMAIN_NOTE_RX = {
    "product": re.compile(r"^\s*product\s+domain\s+note\s*:\s*(.+)$", re.IGNORECASE),
    "customer": re.compile(r"^\s*customer\s+domain\s+note\s*:\s*(.+)$", re.IGNORECASE),
    "revenue": re.compile(r"^\s*revenue\s+domain\s+note\s*:\s*(.+)$", re.IGNORECASE),
    "team": re.compile(r"^\s*team\s+domain\s+note\s*:\s*(.+)$", re.IGNORECASE),
    "project": re.compile(r"^\s*project\s+domain\s+note\s*:\s*(.+)$", re.IGNORECASE),
    "operational": re.compile(r"^\s*operational\s+domain\s+note\s*:\s*(.+)$", re.IGNORECASE),
}

_KIND_BY_DOMAIN = {
    "product": "product_domain_note",
    "customer": "customer_domain_note",
    "revenue": "revenue_domain_note",
    "team": "team_domain_note",
    "project": "project_domain_note",
    "operational": "operational_domain_note",
}

_GOAL_RX = re.compile(r"^\s*business\s+goal\s+note\s*:\s*(.+)$", re.IGNORECASE)
_ALIGNMENT_RX = re.compile(r"^\s*strategic\s+alignment\s+note\s*:\s*(.+)$", re.IGNORECASE)
_CUSTOMER_INSIGHT_RX = re.compile(r"^\s*customer\s+insight\s+note\s*:\s*(.+)$", re.IGNORECASE)
_REVENUE_OBS_RX = re.compile(r"^\s*revenue\s+observation\s+note\s*:\s*(.+)$", re.IGNORECASE)

_DECISION_RX = re.compile(
    r"^\s*business\s+decision\s+(?P<decision>approve|hold|reject|defer)\s*:\s*(?P<body>.+)$",
    re.IGNORECASE | re.S,
)

_KV_RX = re.compile(r"(\w+)\s*=\s*([^,\s]+(?:\s+[^,\s=]+)*)")


def _parse_kv_blob(blob: str) -> dict[str, str]:
    out: dict[str, str] = {}
    for match in _KV_RX.finditer(blob):
        out[match.group(1).lower()] = match.group(2).strip()
    return out


def parse_autonomous_business_operating_system_intent(raw: str) -> dict[str, Any] | None:
    text = str(raw or "").strip()
    if not text:
        return None

    if _VIEW_RX.match(text):
        return {"action": "view"}

    decision_match = _DECISION_RX.match(text)
    if decision_match:
        decision = decision_match.group("decision").lower()
        body = (decision_match.group("body") or "").strip()
        if not body:
            return None
        return {
            "action": "record",
            "kind": f"human_business_decision_{decision}",
            "content": body,
        }

    for domain, rx in _DOMAIN_NOTE_RX.items():
        match = rx.match(text)
        if match:
            kv = _parse_kv_blob(match.group(1))
            return {
                "action": "record",
                "kind": _KIND_BY_DOMAIN[domain],
                "content": match.group(1).strip(),
                "business_domain": domain,
                "opportunity_id": kv.get("opportunity") or kv.get("opportunity_id"),
                "goal_id": kv.get("goal") or kv.get("goal_id"),
            }

    for rx, kind, domain in (
        (_GOAL_RX, "business_goal_note", None),
        (_ALIGNMENT_RX, "strategic_alignment_note", None),
        (_CUSTOMER_INSIGHT_RX, "customer_insight_note", "customer"),
        (_REVENUE_OBS_RX, "revenue_observation_note", "revenue"),
    ):
        match = rx.match(text)
        if match:
            kv = _parse_kv_blob(match.group(1))
            intent: dict[str, Any] = {
                "action": "record",
                "kind": kind,
                "content": match.group(1).strip(),
                "goal_id": kv.get("goal") or kv.get("goal_id"),
                "opportunity_id": kv.get("opportunity") or kv.get("opportunity_id"),
            }
            if domain:
                intent["business_domain"] = domain
            return intent

    lowered = text.lower()
    if lowered.startswith("business operating:") or lowered.startswith("business:"):
        body = text.split(":", 1)[1].strip()
        return {
            "action": "record",
            "kind": "autonomous_business_operating_system_record",
            "content": body,
        }

    return None


def handle_autonomous_business_operating_system_intent(
    intent: dict[str, Any],
    *,
    session_id: str | None = None,
) -> dict[str, Any]:
    action = intent.get("action")
    if action == "view":
        return {"action": "view"}

    if action == "record":
        kind = str(intent.get("kind") or "")
        if kind not in AUTONOMOUS_BUSINESS_OPERATING_SYSTEM_RECORD_KINDS:
            raise ValueError(f"unsupported record kind: {kind!r}")
        domain = intent.get("business_domain")
        if domain and str(domain) not in BUSINESS_DOMAINS:
            raise ValueError(f"unsupported business domain: {domain!r}")
        record = append_autonomous_business_operating_system_record(
            kind=kind,
            content=str(intent.get("content") or ""),
            session_id=session_id,
            business_domain=str(domain) if domain else None,
            goal_id=str(intent.get("goal_id") or "") or None,
            opportunity_id=str(intent.get("opportunity_id") or "") or None,
        )
        return {"action": "record", "record": record}

    raise ValueError(f"unsupported intent action: {action!r}")

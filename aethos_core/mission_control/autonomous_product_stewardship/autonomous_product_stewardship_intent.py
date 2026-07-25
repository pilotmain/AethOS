# SPDX-License-Identifier: Apache-2.0
"""FIX 270 — autonomous product stewardship intent."""

from __future__ import annotations

import re
from typing import Any

from aethos_core.mission_control.autonomous_product_stewardship.autonomous_product_stewardship_contract import (
    AUTONOMOUS_PRODUCT_STEWARDSHIP_RECORD_KINDS,
    PORTFOLIO_REPOSITORIES,
)
from aethos_core.mission_control.autonomous_product_stewardship.autonomous_product_stewardship_store import (
    append_autonomous_product_stewardship_record,
)

_VIEW_RX = re.compile(
    r"^\s*(?:show\s+)?(?:(?:autonomous\s+)?product\s+stewardship(?:\s+(?:dashboard|intelligence|report))?|"
    r"portfolio\s+stewardship(?:\s+dashboard)?|"
    r"stewardship\s+dashboard)\s*$",
    re.IGNORECASE,
)

_PRODUCT_HEALTH_RX = re.compile(r"^\s*product\s+health\s+observation\s*:\s*(.+)$", re.IGNORECASE)
_ENGINEERING_RX = re.compile(r"^\s*engineering\s+stewardship\s+observation\s*:\s*(.+)$", re.IGNORECASE)
_OPERATIONAL_RX = re.compile(r"^\s*operational\s+stewardship\s+observation\s*:\s*(.+)$", re.IGNORECASE)
_GOVERNANCE_RX = re.compile(r"^\s*governance\s+stewardship\s+observation\s*:\s*(.+)$", re.IGNORECASE)
_PORTFOLIO_RX = re.compile(r"^\s*portfolio\s+stewardship\s+observation\s*:\s*(.+)$", re.IGNORECASE)
_OPPORTUNITY_RX = re.compile(r"^\s*stewardship\s+opportunity\s+note\s*:\s*(.+)$", re.IGNORECASE)
_BACKLOG_RX = re.compile(r"^\s*stewardship\s+backlog\s+note\s*:\s*(.+)$", re.IGNORECASE)

_DECISION_RX = re.compile(
    r"^\s*stewardship\s+decision\s+(?P<decision>approve|hold|reject|defer)\s*:\s*(?P<body>.+)$",
    re.IGNORECASE | re.S,
)

_KV_RX = re.compile(r"(\w+)\s*=\s*([^,\s]+(?:\s+[^,\s=]+)*)")


def _parse_kv_blob(blob: str) -> dict[str, str]:
    out: dict[str, str] = {}
    for match in _KV_RX.finditer(blob):
        out[match.group(1).lower()] = match.group(2).strip()
    return out


def parse_autonomous_product_stewardship_intent(raw: str) -> dict[str, Any] | None:
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
            "kind": f"human_stewardship_decision_{decision}",
            "content": body,
        }

    for rx, kind in (
        (_PRODUCT_HEALTH_RX, "product_health_observation"),
        (_ENGINEERING_RX, "engineering_stewardship_observation"),
        (_OPERATIONAL_RX, "operational_stewardship_observation"),
        (_GOVERNANCE_RX, "governance_stewardship_observation"),
        (_PORTFOLIO_RX, "portfolio_stewardship_observation"),
        (_OPPORTUNITY_RX, "stewardship_opportunity_note"),
        (_BACKLOG_RX, "stewardship_backlog_note"),
    ):
        match = rx.match(text)
        if match:
            kv = _parse_kv_blob(match.group(1))
            return {
                "action": "record",
                "kind": kind,
                "content": match.group(1).strip(),
                "repository": kv.get("repository") or kv.get("repo"),
                "domain": kv.get("domain"),
                "opportunity_id": kv.get("opportunity") or kv.get("opportunity_id"),
            }

    lowered = text.lower()
    if lowered.startswith("product stewardship:") or lowered.startswith("stewardship:"):
        body = text.split(":", 1)[1].strip()
        return {
            "action": "record",
            "kind": "autonomous_product_stewardship_record",
            "content": body,
        }

    return None


def handle_autonomous_product_stewardship_intent(
    intent: dict[str, Any],
    *,
    session_id: str | None = None,
) -> dict[str, Any]:
    action = intent.get("action")
    if action == "view":
        return {"action": "view"}

    if action == "record":
        kind = str(intent.get("kind") or "")
        if kind not in AUTONOMOUS_PRODUCT_STEWARDSHIP_RECORD_KINDS:
            raise ValueError(f"unsupported record kind: {kind!r}")
        repo = intent.get("repository")
        if repo and str(repo) not in PORTFOLIO_REPOSITORIES:
            raise ValueError(f"unsupported repository: {repo!r}")
        record = append_autonomous_product_stewardship_record(
            kind=kind,
            content=str(intent.get("content") or ""),
            session_id=session_id,
            repository=str(repo) if repo else None,
            domain=str(intent.get("domain") or "") or None,
            opportunity_id=str(intent.get("opportunity_id") or "") or None,
        )
        return {"action": "record", "record": record}

    raise ValueError(f"unsupported intent action: {action!r}")

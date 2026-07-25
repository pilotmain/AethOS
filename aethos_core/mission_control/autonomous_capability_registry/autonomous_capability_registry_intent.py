# SPDX-License-Identifier: Apache-2.0
"""FIX 295 — autonomous capability registry intent."""

from __future__ import annotations

import re
from typing import Any

from aethos_core.mission_control.autonomous_capability_registry.autonomous_capability_registry_contract import (
    AUTONOMOUS_CAPABILITY_REGISTRY_RECORD_KINDS,
    CAPABILITY_DOMAINS,
)
from aethos_core.mission_control.autonomous_capability_registry.autonomous_capability_registry_store import (
    append_autonomous_capability_registry_record,
)

_VIEW_REGISTRY_RX = re.compile(
    r"^\s*(?:show\s+)?(?:autonomous\s+)?capability\s+registry\s*$",
    re.IGNORECASE,
)
_VIEW_SELF_AWARENESS_RX = re.compile(
    r"^\s*(?:show\s+)?(?:self[\s-]?awareness(?:\s+report)?|"
    r"what(?:\s+are\s+you|\s+can\s+you)\s+capable(?:\s+of(?:\s+doing)?)?|"
    r"what\s+can\s+you\s+do)\s*$",
    re.IGNORECASE,
)
_VIEW_MATURITY_RX = re.compile(
    r"^\s*(?:show\s+)?(?:autonomous\s+)?capability\s+maturity(?:\s+dashboard)?\s*$",
    re.IGNORECASE,
)
_VIEW_DRIFT_RX = re.compile(
    r"^\s*(?:show\s+)?(?:autonomous\s+)?capability\s+drift(?:\s+report)?\s*$",
    re.IGNORECASE,
)
_VIEW_DASHBOARD_RX = re.compile(
    r"^\s*(?:show\s+)?(?:autonomous\s+)?capability(?:\s+operating)?\s+dashboard\s*$",
    re.IGNORECASE,
)

_CAPABILITY_NOTE_RX = re.compile(r"^\s*capability\s+note\s*:\s*(.+)$", re.IGNORECASE)
_EVIDENCE_NOTE_RX = re.compile(r"^\s*capability\s+evidence\s+note\s*:\s*(.+)$", re.IGNORECASE)

_DECISION_RX = re.compile(
    r"^\s*capability\s+review\s+(?P<decision>approve|hold|reject|defer)\s*:\s*(?P<body>.+)$",
    re.IGNORECASE | re.S,
)

_KV_RX = re.compile(r"(\w+)\s*=\s*([^,\s]+)")


def _parse_kv_blob(blob: str) -> dict[str, str]:
    out: dict[str, str] = {}
    for match in _KV_RX.finditer(blob):
        out[match.group(1).lower()] = match.group(2).strip()
    return out


def parse_autonomous_capability_registry_intent(raw: str) -> dict[str, Any] | None:
    text = str(raw or "").strip()
    if not text:
        return None

    if _VIEW_REGISTRY_RX.match(text):
        return {"action": "view", "focus": "registry"}
    if _VIEW_SELF_AWARENESS_RX.match(text):
        return {"action": "view", "focus": "self_awareness"}
    if _VIEW_MATURITY_RX.match(text):
        return {"action": "view", "focus": "maturity"}
    if _VIEW_DRIFT_RX.match(text):
        return {"action": "view", "focus": "drift"}
    if _VIEW_DASHBOARD_RX.match(text):
        return {"action": "view", "focus": "dashboard"}

    decision_match = _DECISION_RX.match(text)
    if decision_match:
        decision = decision_match.group("decision").lower()
        body = (decision_match.group("body") or "").strip()
        if not body:
            return None
        return {
            "action": "record",
            "kind": f"human_capability_review_{decision}",
            "content": body,
        }

    evidence_match = _EVIDENCE_NOTE_RX.match(text)
    if evidence_match:
        kv = _parse_kv_blob(evidence_match.group(1))
        return {
            "action": "record",
            "kind": "capability_evidence_note",
            "content": evidence_match.group(1).strip(),
            "capability_id": kv.get("capability") or kv.get("capability_id"),
            "capability_domain": kv.get("domain") or kv.get("capability_domain"),
        }

    note_match = _CAPABILITY_NOTE_RX.match(text)
    if note_match:
        kv = _parse_kv_blob(note_match.group(1))
        return {
            "action": "record",
            "kind": "capability_note",
            "content": note_match.group(1).strip(),
            "capability_id": kv.get("capability") or kv.get("capability_id"),
            "capability_domain": kv.get("domain") or kv.get("capability_domain"),
        }

    lowered = text.lower()
    if lowered.startswith("capability registry:") or lowered.startswith("capability:"):
        body = text.split(":", 1)[1].strip()
        return {
            "action": "record",
            "kind": "autonomous_capability_registry_record",
            "content": body,
        }

    return None


def handle_autonomous_capability_registry_intent(
    intent: dict[str, Any],
    *,
    session_id: str | None = None,
) -> dict[str, Any]:
    action = intent.get("action")
    if action == "view":
        return {"action": "view", "focus": intent.get("focus") or "dashboard"}

    if action == "record":
        kind = str(intent.get("kind") or "")
        if kind not in AUTONOMOUS_CAPABILITY_REGISTRY_RECORD_KINDS:
            raise ValueError(f"unsupported record kind: {kind!r}")
        domain = intent.get("capability_domain")
        if domain and str(domain) not in CAPABILITY_DOMAINS:
            raise ValueError(f"unsupported capability domain: {domain!r}")
        record = append_autonomous_capability_registry_record(
            kind=kind,
            content=str(intent.get("content") or ""),
            session_id=session_id,
            capability_id=str(intent.get("capability_id") or "") or None,
            capability_domain=str(domain) if domain else None,
        )
        return {"action": "record", "record": record}

    raise ValueError(f"unsupported intent action: {action!r}")

# SPDX-License-Identifier: Apache-2.0
"""WORKSTREAM_G1 / FIX 354 — operator intent parsing."""

from __future__ import annotations

import re
from typing import Any

from aethos_core.workstreams.real_evidence_density_trust_maturity_program.real_evidence_density_trust_maturity_program_contract import (
    EVIDENCE_MATURITY_RECORD_KINDS,
)
from aethos_core.workstreams.real_evidence_density_trust_maturity_program.real_evidence_density_trust_maturity_program_executor import (
    register_evidence_domain_from_text,
)
from aethos_core.workstreams.real_evidence_density_trust_maturity_program.real_evidence_density_trust_maturity_program_store import (
    append_evidence_maturity_record,
)

_DASHBOARD_RX = re.compile(r"^\s*show\s+evidence\s+maturity\s+dashboard\s*$", re.IGNORECASE)
_DOMAIN_RX = re.compile(r"^\s*evidence\s+maturity\s+domain\s*:\s*(?P<body>.+)$", re.IGNORECASE | re.S)
_NOTE_RX = re.compile(r"^\s*evidence\s+maturity\s+note\s*:\s*(?P<body>.+)$", re.IGNORECASE | re.S)
_REVIEW_RX = re.compile(
    r"^\s*evidence\s+maturity\s+review\s+(?P<decision>approve|hold|reject|defer)\s*:\s*(?P<body>.+)$",
    re.IGNORECASE | re.S,
)


def parse_evidence_maturity_intent(raw: str) -> dict[str, Any] | None:
    text = str(raw or "").strip()
    if not text:
        return None

    if _DASHBOARD_RX.match(text):
        return {"action": "view", "focus": "evidence_maturity_dashboard"}

    domain_match = _DOMAIN_RX.match(text)
    if domain_match:
        body = (domain_match.group("body") or "").strip()
        if not body:
            return None
        return {"action": "domain", "body": body}

    note_match = _NOTE_RX.match(text)
    if note_match:
        body = (note_match.group("body") or "").strip()
        if not body:
            return None
        return {"action": "record", "kind": "evidence_maturity_note", "content": body}

    review_match = _REVIEW_RX.match(text)
    if review_match:
        decision = review_match.group("decision").lower()
        body = (review_match.group("body") or "").strip()
        if not body:
            return None
        return {
            "action": "record",
            "kind": f"evidence_maturity_review_{decision}",
            "content": body,
        }

    lowered = text.lower()
    if lowered.startswith("workstream g1:") or lowered.startswith("evidence maturity:"):
        body = text.split(":", 1)[1].strip()
        return {"action": "record", "kind": "evidence_maturity_record", "content": body}

    return None


def handle_evidence_maturity_intent(
    intent: dict[str, Any],
    *,
    session_id: str | None = None,
) -> dict[str, Any]:
    action = intent.get("action")
    sid = (session_id or "default").strip()[:64] or "default"

    if action == "view":
        return {"action": "view", "focus": intent.get("focus") or "evidence_maturity_dashboard"}

    if action == "domain":
        entry = register_evidence_domain_from_text(program_session_id=sid, body=str(intent.get("body") or ""))
        return {"action": "domain", "entry": entry}

    if action == "record":
        kind = str(intent.get("kind") or "")
        if kind not in EVIDENCE_MATURITY_RECORD_KINDS:
            raise ValueError(f"unsupported record kind: {kind!r}")
        record = append_evidence_maturity_record(
            kind=kind,
            content=str(intent.get("content") or ""),
            session_id=sid,
            metadata=dict(intent.get("metadata") or {}),
        )
        return {"action": "record", "record": record}

    raise ValueError(f"unsupported intent action: {action!r}")

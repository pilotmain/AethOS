# SPDX-License-Identifier: Apache-2.0
"""WORKSTREAM_E1 / FIX 343 — operator intent parsing."""

from __future__ import annotations

import re
from typing import Any

from aethos_core.workstreams.intelligence_performance_evidence_scalability_program.intelligence_performance_evidence_scalability_program_contract import (
    INTELLIGENCE_PERFORMANCE_RECORD_KINDS,
)
from aethos_core.workstreams.intelligence_performance_evidence_scalability_program.intelligence_performance_evidence_scalability_program_executor import (
    run_intelligence_performance_analysis,
)
from aethos_core.workstreams.intelligence_performance_evidence_scalability_program.intelligence_performance_evidence_scalability_program_store import (
    append_intelligence_performance_record,
)

_DASHBOARD_RX = re.compile(r"^\s*show\s+intelligence\s+performance\s+dashboard\s*$", re.IGNORECASE)
_ANALYZE_RX = re.compile(r"^\s*analyze\s+intelligence\s+performance\s*$", re.IGNORECASE)

_NOTE_RX = re.compile(r"^\s*performance\s+note\s*:\s*(?P<body>.+)$", re.IGNORECASE | re.S)
_REVIEW_RX = re.compile(
    r"^\s*performance\s+review\s+(?P<decision>approve|hold|reject|defer)\s*:\s*(?P<body>.+)$",
    re.IGNORECASE | re.S,
)


def parse_intelligence_performance_evidence_scalability_intent(raw: str) -> dict[str, Any] | None:
    text = str(raw or "").strip()
    if not text:
        return None

    if _DASHBOARD_RX.match(text):
        return {"action": "view", "focus": "intelligence_performance_dashboard"}
    if _ANALYZE_RX.match(text):
        return {"action": "analyze"}

    note_match = _NOTE_RX.match(text)
    if note_match:
        body = (note_match.group("body") or "").strip()
        if not body:
            return None
        return {"action": "record", "kind": "performance_note", "content": body}

    review_match = _REVIEW_RX.match(text)
    if review_match:
        decision = review_match.group("decision").lower()
        body = (review_match.group("body") or "").strip()
        if not body:
            return None
        return {
            "action": "record",
            "kind": f"performance_review_{decision}",
            "content": body,
        }

    lowered = text.lower()
    if lowered.startswith("workstream e1:") or lowered.startswith("intelligence performance:"):
        body = text.split(":", 1)[1].strip()
        return {"action": "record", "kind": "intelligence_performance_program_record", "content": body}

    return None


def handle_intelligence_performance_evidence_scalability_intent(
    intent: dict[str, Any],
    *,
    session_id: str | None = None,
) -> dict[str, Any]:
    action = intent.get("action")
    sid = (session_id or "default").strip()[:64] or "default"

    if action == "view":
        return {"action": "view", "focus": intent.get("focus") or "intelligence_performance_dashboard"}

    if action == "analyze":
        analysis = run_intelligence_performance_analysis(session_id=sid, use_live_probe=True)
        record = append_intelligence_performance_record(
            session_id=sid,
            kind="performance_analysis_note",
            content="Intelligence performance analysis executed with live fast-module probe",
            metadata={"hotspot_count": analysis.get("compose_hotspot_registry", {}).get("hotspot_count")},
        )
        return {"action": "analyze", "analysis": analysis, "record": record}

    if action == "record":
        kind = str(intent.get("kind") or "")
        if kind not in INTELLIGENCE_PERFORMANCE_RECORD_KINDS:
            raise ValueError(f"unsupported record kind: {kind!r}")
        record = append_intelligence_performance_record(
            kind=kind,
            content=str(intent.get("content") or ""),
            session_id=sid,
            metadata=dict(intent.get("metadata") or {}),
        )
        return {"action": "record", "record": record}

    raise ValueError(f"unsupported intent action: {action!r}")

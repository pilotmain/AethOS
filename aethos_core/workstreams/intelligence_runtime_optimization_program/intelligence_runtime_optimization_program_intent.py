# SPDX-License-Identifier: Apache-2.0
"""WORKSTREAM_E2 / FIX 344 — operator intent parsing."""

from __future__ import annotations

import re
from typing import Any

from aethos_core.workstreams.intelligence_runtime_optimization_program.intelligence_runtime_optimization_program_contract import (
    INTELLIGENCE_RUNTIME_OPTIMIZATION_RECORD_KINDS,
)
from aethos_core.workstreams.intelligence_runtime_optimization_program.intelligence_runtime_optimization_program_executor import (
    run_runtime_optimization_analysis,
)
from aethos_core.workstreams.intelligence_runtime_optimization_program.intelligence_runtime_optimization_program_store import (
    append_intelligence_runtime_optimization_record,
)

_DASHBOARD_RX = re.compile(r"^\s*show\s+runtime\s+optimization\s+dashboard\s*$", re.IGNORECASE)
_ANALYZE_RX = re.compile(r"^\s*analyze\s+runtime\s+optimization\s*$", re.IGNORECASE)

_NOTE_RX = re.compile(r"^\s*runtime\s+optimization\s+note\s*:\s*(?P<body>.+)$", re.IGNORECASE | re.S)
_REVIEW_RX = re.compile(
    r"^\s*runtime\s+optimization\s+review\s+(?P<decision>approve|hold|reject|defer)\s*:\s*(?P<body>.+)$",
    re.IGNORECASE | re.S,
)


def parse_intelligence_runtime_optimization_intent(raw: str) -> dict[str, Any] | None:
    text = str(raw or "").strip()
    if not text:
        return None

    if _DASHBOARD_RX.match(text):
        return {"action": "view", "focus": "runtime_optimization_dashboard"}
    if _ANALYZE_RX.match(text):
        return {"action": "analyze"}

    note_match = _NOTE_RX.match(text)
    if note_match:
        body = (note_match.group("body") or "").strip()
        if not body:
            return None
        return {"action": "record", "kind": "runtime_optimization_note", "content": body}

    review_match = _REVIEW_RX.match(text)
    if review_match:
        decision = review_match.group("decision").lower()
        body = (review_match.group("body") or "").strip()
        if not body:
            return None
        return {
            "action": "record",
            "kind": f"runtime_optimization_review_{decision}",
            "content": body,
        }

    lowered = text.lower()
    if lowered.startswith("workstream e2:") or lowered.startswith("runtime optimization:"):
        body = text.split(":", 1)[1].strip()
        return {"action": "record", "kind": "intelligence_runtime_optimization_program_record", "content": body}

    return None


def handle_intelligence_runtime_optimization_intent(
    intent: dict[str, Any],
    *,
    session_id: str | None = None,
) -> dict[str, Any]:
    action = intent.get("action")
    sid = (session_id or "default").strip()[:64] or "default"

    if action == "view":
        return {"action": "view", "focus": intent.get("focus") or "runtime_optimization_dashboard"}

    if action == "analyze":
        analysis = run_runtime_optimization_analysis(session_id=sid)
        record = append_intelligence_runtime_optimization_record(
            session_id=sid,
            kind="runtime_optimization_probe_note",
            content="Runtime optimization analysis executed with memoization probe",
            metadata={"compose_duration_reduction": analysis.get("runtime_metrics", {}).get("compose_duration_reduction")},
        )
        return {"action": "analyze", "analysis": analysis, "record": record}

    if action == "record":
        kind = str(intent.get("kind") or "")
        if kind not in INTELLIGENCE_RUNTIME_OPTIMIZATION_RECORD_KINDS:
            raise ValueError(f"unsupported record kind: {kind!r}")
        record = append_intelligence_runtime_optimization_record(
            kind=kind,
            content=str(intent.get("content") or ""),
            session_id=sid,
            metadata=dict(intent.get("metadata") or {}),
        )
        return {"action": "record", "record": record}

    raise ValueError(f"unsupported intent action: {action!r}")

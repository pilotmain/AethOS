# SPDX-License-Identifier: Apache-2.0
"""WORKSTREAM_E3 / FIX 345 — operator intent parsing."""

from __future__ import annotations

import re
from typing import Any

from aethos_core.workstreams.intelligence_scalability_implementation_program.intelligence_scalability_implementation_program_contract import (
    INTELLIGENCE_SCALABILITY_RECORD_KINDS,
)
from aethos_core.workstreams.intelligence_scalability_implementation_program.intelligence_scalability_implementation_program_executor import (
    execute_scalability_implementation,
)
from aethos_core.workstreams.intelligence_scalability_implementation_program.intelligence_scalability_implementation_program_store import (
    append_intelligence_scalability_record,
)

_DASHBOARD_RX = re.compile(r"^\s*show\s+intelligence\s+scalability\s+dashboard\s*$", re.IGNORECASE)
_EXECUTE_RX = re.compile(r"^\s*execute\s+scalability\s+implementation\s*$", re.IGNORECASE)

_NOTE_RX = re.compile(r"^\s*scalability\s+note\s*:\s*(?P<body>.+)$", re.IGNORECASE | re.S)
_REVIEW_RX = re.compile(
    r"^\s*scalability\s+review\s+(?P<decision>approve|hold|reject|defer)\s*:\s*(?P<body>.+)$",
    re.IGNORECASE | re.S,
)


def parse_intelligence_scalability_implementation_intent(raw: str) -> dict[str, Any] | None:
    text = str(raw or "").strip()
    if not text:
        return None

    if _DASHBOARD_RX.match(text):
        return {"action": "view", "focus": "intelligence_scalability_dashboard"}
    if _EXECUTE_RX.match(text):
        return {"action": "execute"}

    note_match = _NOTE_RX.match(text)
    if note_match:
        body = (note_match.group("body") or "").strip()
        if not body:
            return None
        return {"action": "record", "kind": "scalability_note", "content": body}

    review_match = _REVIEW_RX.match(text)
    if review_match:
        decision = review_match.group("decision").lower()
        body = (review_match.group("body") or "").strip()
        if not body:
            return None
        return {
            "action": "record",
            "kind": f"scalability_review_{decision}",
            "content": body,
        }

    lowered = text.lower()
    if lowered.startswith("workstream e3:") or lowered.startswith("scalability implementation:"):
        body = text.split(":", 1)[1].strip()
        return {"action": "record", "kind": "intelligence_scalability_implementation_program_record", "content": body}

    return None


def handle_intelligence_scalability_implementation_intent(
    intent: dict[str, Any],
    *,
    session_id: str | None = None,
) -> dict[str, Any]:
    action = intent.get("action")
    sid = (session_id or "default").strip()[:64] or "default"

    if action == "view":
        return {"action": "view", "focus": intent.get("focus") or "intelligence_scalability_dashboard"}

    if action == "execute":
        from aethos_core.workstreams.compose_runtime_guardrails_program.compose_runtime_guard import (
            get_runtime_mode,
        )

        mode = get_runtime_mode(session_id=sid)
        lightweight = mode in {"test", "operator", "lightweight"}
        result = execute_scalability_implementation(session_id=sid, lightweight=lightweight)
        record = append_intelligence_scalability_record(
            session_id=sid,
            kind="scalability_implementation_note",
            content="Scalability implementation executed with memoization, snapshots, and flattening",
            metadata={
                "compose_duration_reduction_pct": (
                    result.get("runtime_benchmark_report") or {}
                ).get("compose_duration_reduction_pct"),
            },
        )
        return {"action": "execute", "result": result, "record": record}

    if action == "record":
        kind = str(intent.get("kind") or "")
        if kind not in INTELLIGENCE_SCALABILITY_RECORD_KINDS:
            raise ValueError(f"unsupported record kind: {kind!r}")
        record = append_intelligence_scalability_record(
            kind=kind,
            content=str(intent.get("content") or ""),
            session_id=sid,
            metadata=dict(intent.get("metadata") or {}),
        )
        return {"action": "record", "record": record}

    raise ValueError(f"unsupported intent action: {action!r}")

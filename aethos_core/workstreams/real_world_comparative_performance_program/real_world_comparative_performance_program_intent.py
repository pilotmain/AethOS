# SPDX-License-Identifier: Apache-2.0
"""PHASE_J2 / FIX 365 — operator intent parsing."""

from __future__ import annotations

import re
from typing import Any

from aethos_core.workstreams.real_world_comparative_performance_program.real_world_comparative_performance_program_contract import (
    COMPARATIVE_PERFORMANCE_RECORD_KINDS,
)
from aethos_core.workstreams.real_world_comparative_performance_program.real_world_comparative_performance_program_executor import (
    register_benchmark_from_text,
)
from aethos_core.workstreams.real_world_comparative_performance_program.real_world_comparative_performance_program_store import (
    append_comparative_performance_record,
)

_DASHBOARD_RX = re.compile(r"^\s*show\s+comparative\s+performance\s+dashboard\s*$", re.IGNORECASE)
_BENCHMARK_RX = re.compile(
    r"^\s*comparative\s+performance\s+benchmark\s*:\s*(?P<body>.+)$",
    re.IGNORECASE | re.S,
)
_NOTE_RX = re.compile(r"^\s*comparative\s+performance\s+note\s*:\s*(?P<body>.+)$", re.IGNORECASE | re.S)
_REVIEW_RX = re.compile(
    r"^\s*comparative\s+performance\s+review\s+(?P<decision>approve|hold|reject|defer)\s*:\s*(?P<body>.+)$",
    re.IGNORECASE | re.S,
)


def parse_comparative_performance_intent(raw: str) -> dict[str, Any] | None:
    text = str(raw or "").strip()
    if not text:
        return None

    if _DASHBOARD_RX.match(text):
        return {"action": "view", "focus": "comparative_performance_dashboard"}

    benchmark_match = _BENCHMARK_RX.match(text)
    if benchmark_match:
        body = (benchmark_match.group("body") or "").strip()
        if not body:
            return None
        return {"action": "benchmark", "body": body}

    note_match = _NOTE_RX.match(text)
    if note_match:
        body = (note_match.group("body") or "").strip()
        if not body:
            return None
        return {"action": "record", "kind": "comparative_performance_note", "content": body}

    review_match = _REVIEW_RX.match(text)
    if review_match:
        decision = review_match.group("decision").lower()
        body = (review_match.group("body") or "").strip()
        if not body:
            return None
        return {
            "action": "record",
            "kind": f"comparative_performance_review_{decision}",
            "content": body,
        }

    lowered = text.lower()
    if lowered.startswith("phase j2:") or lowered.startswith("comparative performance:"):
        body = text.split(":", 1)[1].strip()
        return {"action": "record", "kind": "comparative_performance_record", "content": body}

    return None


def handle_comparative_performance_intent(
    intent: dict[str, Any],
    *,
    session_id: str | None = None,
) -> dict[str, Any]:
    action = intent.get("action")
    sid = (session_id or "default").strip()[:64] or "default"

    if action == "view":
        return {"action": "view", "focus": intent.get("focus") or "comparative_performance_dashboard"}

    if action == "benchmark":
        entry = register_benchmark_from_text(
            program_session_id=sid,
            body=str(intent.get("body") or ""),
        )
        return {"action": "benchmark", "entry": entry}

    if action == "record":
        kind = str(intent.get("kind") or "")
        if kind not in COMPARATIVE_PERFORMANCE_RECORD_KINDS:
            raise ValueError(f"unsupported record kind: {kind!r}")
        record = append_comparative_performance_record(
            kind=kind,
            content=str(intent.get("content") or ""),
            session_id=sid,
            metadata=dict(intent.get("metadata") or {}),
        )
        return {"action": "record", "record": record}

    raise ValueError(f"unsupported intent action: {action!r}")

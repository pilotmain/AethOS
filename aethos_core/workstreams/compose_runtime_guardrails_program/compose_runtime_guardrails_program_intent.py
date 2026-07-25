# SPDX-License-Identifier: Apache-2.0
"""WORKSTREAM_E4 / FIX 346 — operator intent parsing."""

from __future__ import annotations

import re
from typing import Any

from aethos_core.workstreams.compose_runtime_guardrails_program.compose_runtime_guard import (
    BENCHMARK_COMMANDS,
    resolve_benchmark_command,
)
from aethos_core.workstreams.compose_runtime_guardrails_program.compose_runtime_guardrails_program_contract import (
    COMPOSE_RUNTIME_GUARDRAILS_RECORD_KINDS,
)
from aethos_core.workstreams.compose_runtime_guardrails_program.compose_runtime_guardrails_program_executor import (
    enforce_runtime_guardrails,
    run_benchmark_command,
)
from aethos_core.workstreams.compose_runtime_guardrails_program.compose_runtime_guardrails_program_store import (
    append_compose_runtime_guardrails_record,
)

_DASHBOARD_RX = re.compile(r"^\s*show\s+runtime\s+safety\s+dashboard\s*$", re.IGNORECASE)
_ENFORCE_RX = re.compile(r"^\s*enforce\s+runtime\s+guardrails\s*$", re.IGNORECASE)

_NOTE_RX = re.compile(r"^\s*runtime\s+guardrail\s+note\s*:\s*(?P<body>.+)$", re.IGNORECASE | re.S)
_REVIEW_RX = re.compile(
    r"^\s*runtime\s+guardrail\s+review\s+(?P<decision>approve|hold|reject|defer)\s*:\s*(?P<body>.+)$",
    re.IGNORECASE | re.S,
)


def parse_compose_runtime_guardrails_intent(raw: str) -> dict[str, Any] | None:
    text = str(raw or "").strip()
    if not text:
        return None

    if _DASHBOARD_RX.match(text):
        return {"action": "view", "focus": "runtime_safety_dashboard"}
    if _ENFORCE_RX.match(text):
        return {"action": "enforce"}

    benchmark = resolve_benchmark_command(text)
    if benchmark is not None:
        return {"action": "benchmark", "command_text": text, **benchmark}

    if text.lower() in BENCHMARK_COMMANDS:
        benchmark = resolve_benchmark_command(text.lower())
        if benchmark is not None:
            return {"action": "benchmark", "command_text": text.lower(), **benchmark}

    note_match = _NOTE_RX.match(text)
    if note_match:
        body = (note_match.group("body") or "").strip()
        if not body:
            return None
        return {"action": "record", "kind": "runtime_guardrail_note", "content": body}

    review_match = _REVIEW_RX.match(text)
    if review_match:
        decision = review_match.group("decision").lower()
        body = (review_match.group("body") or "").strip()
        if not body:
            return None
        return {
            "action": "record",
            "kind": f"runtime_guardrail_review_{decision}",
            "content": body,
        }

    lowered = text.lower()
    if lowered.startswith("workstream e4:") or lowered.startswith("runtime guardrails:"):
        body = text.split(":", 1)[1].strip()
        return {"action": "record", "kind": "compose_runtime_guardrails_program_record", "content": body}

    return None


def handle_compose_runtime_guardrails_intent(
    intent: dict[str, Any],
    *,
    session_id: str | None = None,
) -> dict[str, Any]:
    action = intent.get("action")
    sid = (session_id or "default").strip()[:64] or "default"

    if action == "view":
        return {"action": "view", "focus": intent.get("focus") or "runtime_safety_dashboard"}

    if action == "enforce":
        result = enforce_runtime_guardrails(session_id=sid)
        record = append_compose_runtime_guardrails_record(
            session_id=sid,
            kind="runtime_guardrail_enforcement_note",
            content="Runtime guardrails enforced for session",
        )
        return {"action": "enforce", "result": result, "record": record}

    if action == "benchmark":
        result = run_benchmark_command(session_id=sid, command_text=str(intent.get("command_text") or ""))
        record = append_compose_runtime_guardrails_record(
            session_id=sid,
            kind="runtime_guardrail_enforcement_note",
            content=f"Benchmark command executed: {intent.get('command_text')}",
            metadata={"command": intent.get("command"), "mode": intent.get("mode")},
        )
        return {"action": "benchmark", "result": result, "record": record}

    if action == "record":
        kind = str(intent.get("kind") or "")
        if kind not in COMPOSE_RUNTIME_GUARDRAILS_RECORD_KINDS:
            raise ValueError(f"unsupported record kind: {kind!r}")
        record = append_compose_runtime_guardrails_record(
            kind=kind,
            content=str(intent.get("content") or ""),
            session_id=sid,
            metadata=dict(intent.get("metadata") or {}),
        )
        return {"action": "record", "record": record}

    raise ValueError(f"unsupported intent action: {action!r}")

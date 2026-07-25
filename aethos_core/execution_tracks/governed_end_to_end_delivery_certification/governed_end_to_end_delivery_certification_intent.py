# SPDX-License-Identifier: Apache-2.0
"""FIX 338 / EXECUTION_TRACK_5 — operator intent parsing."""

from __future__ import annotations

import re
from typing import Any

from aethos_core.execution_tracks.governed_end_to_end_delivery_certification.governed_end_to_end_delivery_certification_contract import (
    CERTIFICATION_SCENARIO_IDS,
    GOVERNED_END_TO_END_DELIVERY_CERTIFICATION_RECORD_KINDS,
)
from aethos_core.execution_tracks.governed_end_to_end_delivery_certification.governed_end_to_end_delivery_certification_executor import (
    run_certification_scenario,
)
from aethos_core.execution_tracks.governed_end_to_end_delivery_certification.governed_end_to_end_delivery_certification_store import (
    append_governed_end_to_end_delivery_certification_record,
)

_DASHBOARD_RX = re.compile(r"^\s*show\s+delivery\s+certification\s+dashboard\s*$", re.IGNORECASE)
_STATUS_RX = re.compile(r"^\s*show\s+delivery\s+certification\s+status\s*$", re.IGNORECASE)

_CERTIFICATION_REVIEW_RX = re.compile(
    r"^\s*certification\s+review\s*:\s*(?P<body>.+)$",
    re.IGNORECASE | re.S,
)
_READINESS_REVIEW_RX = re.compile(
    r"^\s*certification\s+readiness\s+review\s*:\s*(?P<body>.+)$",
    re.IGNORECASE | re.S,
)
_EVIDENCE_REVIEW_RX = re.compile(
    r"^\s*certification\s+evidence\s+review\s*:\s*(?P<body>.+)$",
    re.IGNORECASE | re.S,
)
_DECISION_RX = re.compile(
    r"^\s*certification\s+decision\s+(?P<decision>approve|hold|reject|defer)\s*:\s*(?P<body>.+)$",
    re.IGNORECASE | re.S,
)
_RUN_RX = re.compile(
    r"^\s*certification\s+run\s*:\s*(?P<body>.+)$",
    re.IGNORECASE | re.S,
)

_KV_RX = re.compile(r"(\w+)\s*=\s*([^,\s]+)")


def _parse_kv_blob(blob: str) -> dict[str, str]:
    out: dict[str, str] = {}
    for match in _KV_RX.finditer(blob):
        out[match.group(1).lower()] = match.group(2).strip()
    return out


def _resolve_scenario_id(kv: dict[str, str]) -> str | None:
    scenario = kv.get("scenario") or kv.get("scenario_id") or ""
    if scenario in CERTIFICATION_SCENARIO_IDS:
        return scenario
    aliases = {
        "fastapi_railway": "scenario_1_fastapi_railway",
        "spring_boot_railway": "scenario_2_spring_boot_railway",
        "nextjs_vercel": "scenario_3_nextjs_vercel",
        "bug_fix": "scenario_4_bug_fix_delivery",
        "documentation": "scenario_5_documentation_change",
    }
    return aliases.get(scenario.lower())


def parse_governed_end_to_end_delivery_certification_intent(raw: str) -> dict[str, Any] | None:
    text = str(raw or "").strip()
    if not text:
        return None

    if _DASHBOARD_RX.match(text):
        return {"action": "view", "focus": "delivery_certification_dashboard"}
    if _STATUS_RX.match(text):
        return {"action": "view", "focus": "delivery_certification_status"}

    run_match = _RUN_RX.match(text)
    if run_match:
        body = (run_match.group("body") or "").strip()
        kv = _parse_kv_blob(body)
        scenario_id = _resolve_scenario_id(kv)
        if not scenario_id:
            return None
        return {"action": "run", "scenario_id": scenario_id, "metadata": kv}

    for rx, kind in (
        (_CERTIFICATION_REVIEW_RX, "certification_review_note"),
        (_READINESS_REVIEW_RX, "certification_readiness_review_note"),
        (_EVIDENCE_REVIEW_RX, "certification_evidence_review_note"),
    ):
        match = rx.match(text)
        if match:
            body = (match.group("body") or "").strip()
            kv = _parse_kv_blob(body)
            return {
                "action": "record",
                "kind": kind,
                "content": body,
                "metadata": {
                    "scenario_id": _resolve_scenario_id(kv),
                    "provider": kv.get("provider"),
                    "environment": kv.get("environment") or kv.get("env"),
                },
            }

    decision_match = _DECISION_RX.match(text)
    if decision_match:
        decision = decision_match.group("decision").lower()
        body = (decision_match.group("body") or "").strip()
        if not body:
            return None
        return {
            "action": "record",
            "kind": f"certification_decision_{decision}",
            "content": body,
        }

    lowered = text.lower()
    if lowered.startswith("execution track 5:") or lowered.startswith("delivery certification:"):
        body = text.split(":", 1)[1].strip()
        return {
            "action": "record",
            "kind": "governed_end_to_end_delivery_certification_record",
            "content": body,
        }

    return None


def handle_governed_end_to_end_delivery_certification_intent(
    intent: dict[str, Any],
    *,
    session_id: str | None = None,
) -> dict[str, Any]:
    action = intent.get("action")
    sid = (session_id or "default").strip()[:64] or "default"

    if action == "view":
        return {"action": "view", "focus": intent.get("focus") or "delivery_certification_dashboard"}

    if action == "run":
        scenario_id = str(intent.get("scenario_id") or "")
        run = run_certification_scenario(session_id=sid, scenario_id=scenario_id)
        return {"action": "run", "scenario_id": scenario_id, "run": run}

    if action == "record":
        kind = str(intent.get("kind") or "")
        if kind not in GOVERNED_END_TO_END_DELIVERY_CERTIFICATION_RECORD_KINDS:
            raise ValueError(f"unsupported record kind: {kind!r}")
        record = append_governed_end_to_end_delivery_certification_record(
            kind=kind,
            content=str(intent.get("content") or ""),
            session_id=sid,
            metadata=dict(intent.get("metadata") or {}),
        )
        return {"action": "record", "record": record}

    raise ValueError(f"unsupported intent action: {action!r}")

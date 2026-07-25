# SPDX-License-Identifier: Apache-2.0
"""FIX 337 / EXECUTION_TRACK_4 — operator intent parsing."""

from __future__ import annotations

import re
from typing import Any

from aethos_core.execution_tracks.governed_deployment_execution.governed_deployment_execution_contract import (
    GOVERNED_DEPLOYMENT_EXECUTION_RECORD_KINDS,
)
from aethos_core.execution_tracks.governed_deployment_execution.governed_deployment_execution_executor import (
    execute_deployment,
)
from aethos_core.execution_tracks.governed_deployment_execution.governed_deployment_execution_store import (
    append_governed_deployment_execution_record,
)

_DASHBOARD_RX = re.compile(r"^\s*show\s+deployment\s+dashboard\s*$", re.IGNORECASE)
_VERIFICATION_RX = re.compile(r"^\s*show\s+deployment\s+verification\s*$", re.IGNORECASE)

_DEPLOYMENT_REVIEW_RX = re.compile(
    r"^\s*deployment\s+review\s*:\s*(?P<body>.+)$",
    re.IGNORECASE | re.S,
)
_READINESS_REVIEW_RX = re.compile(
    r"^\s*deployment\s+readiness\s+review\s*:\s*(?P<body>.+)$",
    re.IGNORECASE | re.S,
)
_EXECUTION_REVIEW_RX = re.compile(
    r"^\s*deployment\s+execution\s+review\s*:\s*(?P<body>.+)$",
    re.IGNORECASE | re.S,
)
_DECISION_RX = re.compile(
    r"^\s*deployment\s+decision\s+(?P<decision>approve|hold|reject|defer)\s*:\s*(?P<body>.+)$",
    re.IGNORECASE | re.S,
)

_KV_RX = re.compile(r"(\w+)\s*=\s*([^,\s]+)")


def _parse_kv_blob(blob: str) -> dict[str, str]:
    out: dict[str, str] = {}
    for match in _KV_RX.finditer(blob):
        out[match.group(1).lower()] = match.group(2).strip()
    return out


def parse_governed_deployment_execution_intent(raw: str) -> dict[str, Any] | None:
    text = str(raw or "").strip()
    if not text:
        return None

    if _DASHBOARD_RX.match(text):
        return {"action": "view", "focus": "deployment_execution_dashboard"}
    if _VERIFICATION_RX.match(text):
        return {"action": "view", "focus": "deployment_verification"}

    for rx, kind in (
        (_DEPLOYMENT_REVIEW_RX, "deployment_review_note"),
        (_READINESS_REVIEW_RX, "deployment_readiness_review_note"),
        (_EXECUTION_REVIEW_RX, "deployment_execution_review_note"),
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
                    "provider": kv.get("provider"),
                    "environment": kv.get("environment") or kv.get("env"),
                    "target": kv.get("target") or kv.get("service") or kv.get("project"),
                    "production_approved": kv.get("production_approved") or kv.get("production"),
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
            "kind": f"deployment_decision_{decision}",
            "content": body,
        }

    lowered = text.lower()
    if lowered.startswith("execution track 4:") or lowered.startswith("deployment execution:"):
        body = text.split(":", 1)[1].strip()
        return {
            "action": "record",
            "kind": "governed_deployment_execution_record",
            "content": body,
        }

    return None


def handle_governed_deployment_execution_intent(
    intent: dict[str, Any],
    *,
    session_id: str | None = None,
) -> dict[str, Any]:
    action = intent.get("action")
    sid = (session_id or "default").strip()[:64] or "default"

    if action == "view":
        return {"action": "view", "focus": intent.get("focus") or "deployment_execution_dashboard"}

    if action == "record":
        kind = str(intent.get("kind") or "")
        if kind not in GOVERNED_DEPLOYMENT_EXECUTION_RECORD_KINDS:
            raise ValueError(f"unsupported record kind: {kind!r}")
        record = append_governed_deployment_execution_record(
            kind=kind,
            content=str(intent.get("content") or ""),
            session_id=sid,
            metadata=dict(intent.get("metadata") or {}),
        )
        result: dict[str, Any] = {"action": "record", "record": record}
        if kind == "deployment_decision_approve":
            deployment = execute_deployment(session_id=sid)
            result["deployment"] = deployment
        return result

    raise ValueError(f"unsupported intent action: {action!r}")

# SPDX-License-Identifier: Apache-2.0
"""FIX 336 / EXECUTION_TRACK_3 — operator intent parsing."""

from __future__ import annotations

import re
from typing import Any

from aethos_core.execution_tracks.governed_git_delivery.governed_git_delivery_contract import (
    GOVERNED_GIT_DELIVERY_RECORD_KINDS,
)
from aethos_core.execution_tracks.governed_git_delivery.governed_git_delivery_executor import (
    execute_git_delivery,
)
from aethos_core.execution_tracks.governed_git_delivery.governed_git_delivery_store import (
    append_governed_git_delivery_record,
)

_DASHBOARD_RX = re.compile(r"^\s*show\s+git\s+delivery\s+dashboard\s*$", re.IGNORECASE)
_VERIFICATION_RX = re.compile(r"^\s*show\s+delivery\s+verification\s*$", re.IGNORECASE)

_DELIVERY_REVIEW_RX = re.compile(
    r"^\s*git\s+delivery\s+review\s*:\s*(?P<body>.+)$",
    re.IGNORECASE | re.S,
)
_BRANCH_REVIEW_RX = re.compile(
    r"^\s*branch\s+delivery\s+review\s*:\s*(?P<body>.+)$",
    re.IGNORECASE | re.S,
)
_COMMIT_REVIEW_RX = re.compile(
    r"^\s*commit\s+delivery\s+review\s*:\s*(?P<body>.+)$",
    re.IGNORECASE | re.S,
)
_PR_REVIEW_RX = re.compile(
    r"^\s*pull\s+request\s+review\s*:\s*(?P<body>.+)$",
    re.IGNORECASE | re.S,
)
_DECISION_RX = re.compile(
    r"^\s*git\s+delivery\s+decision\s+(?P<decision>approve|hold|reject|defer)\s*:\s*(?P<body>.+)$",
    re.IGNORECASE | re.S,
)

_KV_RX = re.compile(r"(\w+)\s*=\s*([^,\s]+)")


def _parse_kv_blob(blob: str) -> dict[str, str]:
    out: dict[str, str] = {}
    for match in _KV_RX.finditer(blob):
        out[match.group(1).lower()] = match.group(2).strip()
    return out


def parse_governed_git_delivery_intent(raw: str) -> dict[str, Any] | None:
    text = str(raw or "").strip()
    if not text:
        return None

    if _DASHBOARD_RX.match(text):
        return {"action": "view", "focus": "git_delivery_dashboard"}
    if _VERIFICATION_RX.match(text):
        return {"action": "view", "focus": "git_delivery_verification"}

    for rx, kind in (
        (_DELIVERY_REVIEW_RX, "git_delivery_review_note"),
        (_BRANCH_REVIEW_RX, "branch_delivery_review_note"),
        (_COMMIT_REVIEW_RX, "commit_delivery_review_note"),
        (_PR_REVIEW_RX, "pull_request_review_note"),
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
                    "work_item": kv.get("work_item") or kv.get("feature") or kv.get("feature_name"),
                    "repository": kv.get("repository") or kv.get("repo"),
                    "target_branch": kv.get("target_branch") or kv.get("base_branch") or kv.get("base"),
                    "changeset_id": kv.get("changeset") or kv.get("changeset_id"),
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
            "kind": f"git_delivery_decision_{decision}",
            "content": body,
        }

    lowered = text.lower()
    if lowered.startswith("execution track 3:") or lowered.startswith("git delivery:"):
        body = text.split(":", 1)[1].strip()
        return {
            "action": "record",
            "kind": "governed_git_delivery_record",
            "content": body,
        }

    return None


def handle_governed_git_delivery_intent(
    intent: dict[str, Any],
    *,
    session_id: str | None = None,
) -> dict[str, Any]:
    action = intent.get("action")
    sid = (session_id or "default").strip()[:64] or "default"

    if action == "view":
        return {"action": "view", "focus": intent.get("focus") or "git_delivery_dashboard"}

    if action == "record":
        kind = str(intent.get("kind") or "")
        if kind not in GOVERNED_GIT_DELIVERY_RECORD_KINDS:
            raise ValueError(f"unsupported record kind: {kind!r}")
        record = append_governed_git_delivery_record(
            kind=kind,
            content=str(intent.get("content") or ""),
            session_id=sid,
            metadata=dict(intent.get("metadata") or {}),
        )
        result: dict[str, Any] = {"action": "record", "record": record}
        if kind == "git_delivery_decision_approve":
            delivery = execute_git_delivery(session_id=sid)
            result["delivery"] = delivery
        return result

    raise ValueError(f"unsupported intent action: {action!r}")

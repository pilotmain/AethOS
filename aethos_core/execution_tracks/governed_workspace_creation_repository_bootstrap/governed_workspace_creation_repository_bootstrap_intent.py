# SPDX-License-Identifier: Apache-2.0
"""FIX 334 / EXECUTION_TRACK_1 — operator intent parsing."""

from __future__ import annotations

import re
from typing import Any

from aethos_core.execution_tracks.governed_workspace_creation_repository_bootstrap.governed_workspace_creation_repository_bootstrap_contract import (
    GOVERNED_WORKSPACE_CREATION_RECORD_KINDS,
)
from aethos_core.execution_tracks.governed_workspace_creation_repository_bootstrap.governed_workspace_creation_repository_bootstrap_executor import (
    execute_repository_bootstrap,
)
from aethos_core.execution_tracks.governed_workspace_creation_repository_bootstrap.governed_workspace_creation_repository_bootstrap_store import (
    append_governed_workspace_creation_record,
)

_DASHBOARD_RX = re.compile(r"^\s*show\s+workspace\s+dashboard\s*$", re.IGNORECASE)
_BOOTSTRAP_VIEW_RX = re.compile(r"^\s*show\s+repository\s+bootstrap\s*$", re.IGNORECASE)

_CREATE_REVIEW_RX = re.compile(
    r"^\s*create\s+workspace\s+review\s*:\s*(?P<body>.+)$",
    re.IGNORECASE | re.S,
)
_BOOTSTRAP_REVIEW_RX = re.compile(
    r"^\s*workspace\s+bootstrap\s+review\s*:\s*(?P<body>.+)$",
    re.IGNORECASE | re.S,
)
_DECISION_RX = re.compile(
    r"^\s*workspace\s+decision\s+(?P<decision>approve|hold|reject|defer)\s*:\s*(?P<body>.+)$",
    re.IGNORECASE | re.S,
)

_KV_RX = re.compile(r"(\w+)\s*=\s*([^,\s]+)")


def _parse_kv_blob(blob: str) -> dict[str, str]:
    out: dict[str, str] = {}
    for match in _KV_RX.finditer(blob):
        out[match.group(1).lower()] = match.group(2).strip()
    return out


def parse_governed_workspace_creation_intent(raw: str) -> dict[str, Any] | None:
    text = str(raw or "").strip()
    if not text:
        return None

    if _DASHBOARD_RX.match(text):
        return {"action": "view", "focus": "workspace_creation_dashboard"}
    if _BOOTSTRAP_VIEW_RX.match(text):
        return {"action": "view", "focus": "repository_bootstrap_report"}

    create_match = _CREATE_REVIEW_RX.match(text)
    if create_match:
        body = (create_match.group("body") or "").strip()
        kv = _parse_kv_blob(body)
        return {
            "action": "record",
            "kind": "workspace_creation_review_note",
            "content": body,
            "metadata": {
                "workspace_name": kv.get("name") or kv.get("workspace_name") or "governed-workspace",
                "template_id": kv.get("template") or kv.get("template_id") or "generic_repository",
                "org_id": kv.get("org") or kv.get("org_id") or kv.get("organization_id"),
                "tenant_id": kv.get("tenant") or kv.get("tenant_id"),
                "project_name": kv.get("project") or kv.get("project_name"),
            },
        }

    bootstrap_match = _BOOTSTRAP_REVIEW_RX.match(text)
    if bootstrap_match:
        body = (bootstrap_match.group("body") or "").strip()
        kv = _parse_kv_blob(body)
        return {
            "action": "record",
            "kind": "workspace_bootstrap_review_note",
            "content": body,
            "metadata": {
                "template_id": kv.get("template") or kv.get("template_id") or "generic_repository",
                "workspace_name": kv.get("name") or kv.get("workspace_name"),
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
            "kind": f"workspace_decision_{decision}",
            "content": body,
        }

    lowered = text.lower()
    if lowered.startswith("execution track 1:") or lowered.startswith("workspace creation:"):
        body = text.split(":", 1)[1].strip()
        return {
            "action": "record",
            "kind": "governed_workspace_creation_record",
            "content": body,
        }

    return None


def handle_governed_workspace_creation_intent(
    intent: dict[str, Any],
    *,
    session_id: str | None = None,
) -> dict[str, Any]:
    action = intent.get("action")
    sid = (session_id or "default").strip()[:64] or "default"

    if action == "view":
        return {"action": "view", "focus": intent.get("focus") or "workspace_creation_dashboard"}

    if action == "record":
        kind = str(intent.get("kind") or "")
        if kind not in GOVERNED_WORKSPACE_CREATION_RECORD_KINDS:
            raise ValueError(f"unsupported record kind: {kind!r}")
        record = append_governed_workspace_creation_record(
            kind=kind,
            content=str(intent.get("content") or ""),
            session_id=sid,
            metadata=dict(intent.get("metadata") or {}),
        )
        result: dict[str, Any] = {"action": "record", "record": record}
        if kind == "workspace_decision_approve":
            bootstrap = execute_repository_bootstrap(session_id=sid)
            result["bootstrap"] = bootstrap
        return result

    raise ValueError(f"unsupported intent action: {action!r}")

# SPDX-License-Identifier: Apache-2.0
"""FIX 300 — multi-tenant platform foundation intent."""

from __future__ import annotations

import re
from typing import Any

from aethos_core.mission_control.multi_tenant_platform_foundation.multi_tenant_platform_foundation_contract import (
    MULTI_TENANT_PLATFORM_FOUNDATION_RECORD_KINDS,
    TENANT_DOMAINS,
)
from aethos_core.mission_control.multi_tenant_platform_foundation.multi_tenant_platform_foundation_store import (
    append_multi_tenant_platform_foundation_record,
)

_VIEW_DASHBOARD_RX = re.compile(
    r"^\s*(?:show\s+)?(?:(?:multi[\s-]?tenant|tenant)\s+(?:platform(?:\s+foundation)?|dashboard)|"
    r"multi[\s-]?tenant\s+platform\s+foundation)\s*$",
    re.IGNORECASE,
)

_REVIEW_RX = {
    "organization_create_review_note": re.compile(
        r"^\s*organization\s+create\s+review\s*:\s*(.+)$",
        re.IGNORECASE,
    ),
    "workspace_create_review_note": re.compile(
        r"^\s*workspace\s+create\s+review\s*:\s*(.+)$",
        re.IGNORECASE,
    ),
    "project_registration_review_note": re.compile(
        r"^\s*project\s+registration\s+review\s*:\s*(.+)$",
        re.IGNORECASE,
    ),
    "membership_review_note": re.compile(
        r"^\s*membership\s+review\s*:\s*(.+)$",
        re.IGNORECASE,
    ),
    "tenant_governance_review_note": re.compile(
        r"^\s*tenant\s+governance\s+review\s*:\s*(.+)$",
        re.IGNORECASE,
    ),
}

_DECISION_RX = re.compile(
    r"^\s*tenant\s+governance\s+review\s+(?P<decision>approve|hold|reject|defer)\s*:\s*(?P<body>.+)$",
    re.IGNORECASE | re.S,
)

_KV_RX = re.compile(r"(\w+)\s*=\s*([^,\s]+)")


def _parse_kv_blob(blob: str) -> dict[str, str]:
    out: dict[str, str] = {}
    for match in _KV_RX.finditer(blob):
        out[match.group(1).lower()] = match.group(2).strip()
    return out


def parse_multi_tenant_platform_foundation_intent(raw: str) -> dict[str, Any] | None:
    text = str(raw or "").strip()
    if not text:
        return None

    if _VIEW_DASHBOARD_RX.match(text):
        return {"action": "view"}

    decision_match = _DECISION_RX.match(text)
    if decision_match:
        decision = decision_match.group("decision").lower()
        body = (decision_match.group("body") or "").strip()
        if not body:
            return None
        return {
            "action": "record",
            "kind": f"human_tenant_decision_{decision}",
            "content": body,
            "tenant_domain": "governance_isolation",
        }

    for kind, rx in _REVIEW_RX.items():
        match = rx.match(text)
        if match:
            kv = _parse_kv_blob(match.group(1))
            domain = {
                "organization_create_review_note": "organizations",
                "workspace_create_review_note": "workspaces",
                "project_registration_review_note": "projects",
                "membership_review_note": "identity",
                "tenant_governance_review_note": "governance_isolation",
            }[kind]
            return {
                "action": "record",
                "kind": kind,
                "content": match.group(1).strip(),
                "tenant_domain": domain,
                "organization_id": kv.get("organization") or kv.get("organization_id") or kv.get("org"),
                "workspace_id": kv.get("workspace") or kv.get("workspace_id"),
                "project_id": kv.get("project") or kv.get("project_id"),
            }

    lowered = text.lower()
    if lowered.startswith("multi-tenant:") or lowered.startswith("tenant:"):
        body = text.split(":", 1)[1].strip()
        return {
            "action": "record",
            "kind": "multi_tenant_platform_foundation_record",
            "content": body,
        }

    return None


def handle_multi_tenant_platform_foundation_intent(
    intent: dict[str, Any],
    *,
    session_id: str | None = None,
) -> dict[str, Any]:
    action = intent.get("action")
    if action == "view":
        return {"action": "view"}

    if action == "record":
        kind = str(intent.get("kind") or "")
        if kind not in MULTI_TENANT_PLATFORM_FOUNDATION_RECORD_KINDS:
            raise ValueError(f"unsupported record kind: {kind!r}")
        domain = intent.get("tenant_domain")
        if domain and str(domain) not in TENANT_DOMAINS:
            raise ValueError(f"unsupported tenant domain: {domain!r}")
        record = append_multi_tenant_platform_foundation_record(
            kind=kind,
            content=str(intent.get("content") or ""),
            session_id=session_id,
            tenant_domain=str(domain) if domain else None,
            organization_id=str(intent.get("organization_id") or "") or None,
            workspace_id=str(intent.get("workspace_id") or "") or None,
            project_id=str(intent.get("project_id") or "") or None,
        )
        return {"action": "record", "record": record}

    raise ValueError(f"unsupported intent action: {action!r}")

# SPDX-License-Identifier: Apache-2.0
"""FIX 307 — customer usage & audit portal evaluator."""

from __future__ import annotations

from typing import Any

from aethos_core.mission_control.customer_usage_audit_portal.customer_usage_audit_portal_contract import (
    GOVERNANCE_RECORD_KIND_MARKERS,
    USAGE_RECORD_KIND_MARKERS,
)
from aethos_core.mission_control.identity_access_hardening.identity_access_hardening_evaluator import (
    evaluate_access_request,
    evaluate_tenant_boundary,
)


def evaluate_audit_portal_access(
    *,
    role: str,
    requester_org_id: str,
    target_org_id: str | None = None,
) -> dict[str, Any]:
    boundary = evaluate_tenant_boundary(
        requester_org_id=requester_org_id,
        target_org_id=target_org_id or requester_org_id,
    )
    view_eval = evaluate_access_request(
        role=role,
        permission="view",
        requester_org_id=requester_org_id,
        target_org_id=target_org_id or requester_org_id,
    )
    return {
        "allowed": boundary["allowed"] and view_eval["allowed"],
        "role": role,
        "requester_org_id": requester_org_id,
        "target_org_id": target_org_id or requester_org_id,
        "tenant_boundary_passed": boundary["allowed"],
        "view_permission_passed": view_eval["allowed"],
        "cross_tenant_audit_access_enabled": False,
        "reason": boundary.get("reason") or view_eval.get("reason"),
    }


def _kind_category(kind: str) -> str:
    lowered = str(kind or "").lower()
    if any(marker in lowered for marker in GOVERNANCE_RECORD_KIND_MARKERS):
        return "governance"
    if any(marker in lowered for marker in USAGE_RECORD_KIND_MARKERS):
        return "usage"
    return "activity"


def normalize_audit_entry(
    *,
    entry: dict[str, Any],
    source: str,
    org_id: str,
) -> dict[str, Any] | None:
    entry_org = str(entry.get("org_id") or entry.get("organization_id") or org_id or "")
    if entry_org and entry_org != org_id:
        return None
    kind = str(entry.get("kind") or entry.get("action") or entry.get("what") or "record")
    when = entry.get("recorded_at") or entry.get("at") or entry.get("when")
    who = entry.get("actor_id") or entry.get("user_id") or entry.get("who") or entry.get("session_id")
    return {
        "entry_id": entry.get("attribution_id")
        or entry.get("approval_id")
        or entry.get("record_id")
        or f"{source}-{kind}-{when}",
        "source": source,
        "kind": kind,
        "category": _kind_category(kind),
        "who": who,
        "when": when,
        "what": entry.get("content") or entry.get("action") or entry.get("what") or kind,
        "resource_type": entry.get("resource_type"),
        "resource_id": entry.get("resource_id"),
        "approved": entry.get("approved"),
        "immutable": entry.get("immutable", True),
        "read_only": True,
    }


def split_timelines(entries: list[dict[str, Any]]) -> dict[str, list[dict[str, Any]]]:
    activity: list[dict[str, Any]] = []
    governance: list[dict[str, Any]] = []
    usage: list[dict[str, Any]] = []
    for entry in entries:
        category = entry.get("category")
        if category == "governance":
            governance.append(entry)
        elif category == "usage":
            usage.append(entry)
        else:
            activity.append(entry)
    return {
        "activity_timeline": activity,
        "governance_timeline": governance,
        "usage_timeline": usage,
    }

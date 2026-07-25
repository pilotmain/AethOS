# SPDX-License-Identifier: Apache-2.0
"""FIX 301 — tenant onboarding and activation intent."""

from __future__ import annotations

import re
from typing import Any

from aethos_core.mission_control.tenant_onboarding_activation.tenant_onboarding_activation_contract import (
    TENANT_ONBOARDING_ACTIVATION_RECORD_KINDS,
)
from aethos_core.mission_control.tenant_onboarding_activation.tenant_onboarding_activation_store import (
    append_tenant_onboarding_activation_record,
)

_VIEW_ONBOARDING_RX = re.compile(
    r"^\s*(?:show|start)\s+tenant\s+onboarding\s*$",
    re.IGNORECASE,
)

_START_USING_RX = re.compile(
    r"^\s*(?:"
    r"how\s+do\s+i\s+(?:start\s+using|get\s+started\s+with|begin\s+with)\s+aethos"
    r"|how\s+(?:do\s+i\s+)?get\s+started(?:\s+with\s+aethos)?"
    r"|how\s+do\s+i\s+start\s+using\s+aethos"
    r")\s*\??\s*$",
    re.IGNORECASE,
)

_REVIEW_RX = {
    "organization_setup_review_note": re.compile(
        r"^\s*organization\s+setup\s*:\s*(.+)$",
        re.IGNORECASE,
    ),
    "workspace_setup_review_note": re.compile(
        r"^\s*workspace\s+setup\s*:\s*(.+)$",
        re.IGNORECASE,
    ),
    "project_registration_review_note": re.compile(
        r"^\s*project\s+registration\s*:\s*(.+)$",
        re.IGNORECASE,
    ),
    "provider_connection_note": re.compile(
        r"^\s*provider\s+connection\s+note\s*:\s*(.+)$",
        re.IGNORECASE,
    ),
}

_DECISION_RX = re.compile(
    r"^\s*onboarding\s+decision\s+(?P<decision>approve|hold|reject|defer)\s*:\s*(?P<body>.+)$",
    re.IGNORECASE | re.S,
)

_KV_RX = re.compile(r"(\w+)\s*=\s*([^,\s]+)")


def _parse_kv_blob(blob: str) -> dict[str, str]:
    out: dict[str, str] = {}
    for match in _KV_RX.finditer(blob):
        out[match.group(1).lower()] = match.group(2).strip()
    return out


def is_tenant_onboarding_activation_question(text: str) -> bool:
    raw = (text or "").strip()
    if not raw:
        return False
    return bool(_VIEW_ONBOARDING_RX.match(raw) or _START_USING_RX.match(raw))


def parse_tenant_onboarding_activation_intent(raw: str) -> dict[str, Any] | None:
    text = str(raw or "").strip()
    if not text:
        return None

    if _VIEW_ONBOARDING_RX.match(text) or _START_USING_RX.match(text):
        return {"action": "view"}

    decision_match = _DECISION_RX.match(text)
    if decision_match:
        decision = decision_match.group("decision").lower()
        body = (decision_match.group("body") or "").strip()
        if not body:
            return None
        return {
            "action": "record",
            "kind": f"onboarding_decision_{decision}",
            "content": body,
            "onboarding_step": "first_mission_control_session",
        }

    for kind, rx in _REVIEW_RX.items():
        match = rx.match(text)
        if match:
            kv = _parse_kv_blob(match.group(1))
            step = {
                "organization_setup_review_note": "organization_setup",
                "workspace_setup_review_note": "workspace_setup",
                "project_registration_review_note": "project_registration",
                "provider_connection_note": "provider_connection",
            }[kind]
            return {
                "action": "record",
                "kind": kind,
                "content": match.group(1).strip(),
                "onboarding_step": step,
                "organization_id": kv.get("organization") or kv.get("organization_id") or kv.get("org"),
                "workspace_id": kv.get("workspace") or kv.get("workspace_id"),
                "project_id": kv.get("project") or kv.get("project_id"),
            }

    lowered = text.lower()
    if lowered.startswith("tenant onboarding:") or lowered.startswith("onboarding:"):
        body = text.split(":", 1)[1].strip()
        return {
            "action": "record",
            "kind": "tenant_onboarding_activation_record",
            "content": body,
        }

    return None


def handle_tenant_onboarding_activation_intent(
    intent: dict[str, Any],
    *,
    session_id: str | None = None,
) -> dict[str, Any]:
    action = intent.get("action")
    if action == "view":
        return {"action": "view"}

    if action == "record":
        kind = str(intent.get("kind") or "")
        if kind not in TENANT_ONBOARDING_ACTIVATION_RECORD_KINDS:
            raise ValueError(f"unsupported record kind: {kind!r}")
        record = append_tenant_onboarding_activation_record(
            kind=kind,
            content=str(intent.get("content") or ""),
            session_id=session_id,
            onboarding_step=str(intent.get("onboarding_step") or "") or None,
            organization_id=str(intent.get("organization_id") or "") or None,
            workspace_id=str(intent.get("workspace_id") or "") or None,
            project_id=str(intent.get("project_id") or "") or None,
        )
        return {"action": "record", "record": record}

    raise ValueError(f"unsupported intent action: {action!r}")

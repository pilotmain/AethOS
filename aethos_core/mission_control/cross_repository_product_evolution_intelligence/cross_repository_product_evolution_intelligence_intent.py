# SPDX-License-Identifier: Apache-2.0
"""FIX 261 — cross-repository product evolution intelligence intent."""

from __future__ import annotations

import re
from typing import Any

from aethos_core.mission_control.cross_repository_product_evolution_intelligence.cross_repository_product_evolution_intelligence_contract import (
    CROSS_REPOSITORY_PRODUCT_EVOLUTION_INTELLIGENCE_RECORD_KINDS,
    PORTFOLIO_REPOSITORIES,
)
from aethos_core.mission_control.cross_repository_product_evolution_intelligence.cross_repository_product_evolution_intelligence_store import (
    append_cross_repository_product_evolution_intelligence_record,
)

_VIEW_RX = re.compile(
    r"^\s*(?:show\s+)?(?:cross[-\s]?repo(?:sitory)?\s+product\s+evolution\s+intelligence|"
    r"product\s+evolution\s+(?:dashboard|intelligence)|"
    r"portfolio\s+evolution\s+(?:dashboard|intelligence|backlog))\s*$",
    re.IGNORECASE,
)

_FEATURE_RX = re.compile(r"^\s*feature\s+evolution\s+note\s*:\s*(.+)$", re.IGNORECASE)
_QUALITY_RX = re.compile(r"^\s*quality\s+evolution\s+note\s*:\s*(.+)$", re.IGNORECASE)
_ARCH_RX = re.compile(r"^\s*architecture\s+evolution\s+note\s*:\s*(.+)$", re.IGNORECASE)
_OPS_RX = re.compile(r"^\s*operational\s+evolution\s+note\s*:\s*(.+)$", re.IGNORECASE)
_UX_RX = re.compile(r"^\s*ux\s+evolution\s+note\s*:\s*(.+)$", re.IGNORECASE)
_GRAPH_RX = re.compile(r"^\s*opportunity\s+graph\s+note\s*:\s*(.+)$", re.IGNORECASE)
_BACKLOG_RX = re.compile(r"^\s*evolution\s+backlog\s+note\s*:\s*(.+)$", re.IGNORECASE)

_DECISION_RX = re.compile(
    r"^\s*evolution\s+decision\s+(?P<decision>approve|hold|reject|defer)\s*:\s*(?P<body>.+)$",
    re.IGNORECASE | re.S,
)

_KV_RX = re.compile(r"(\w+)\s*=\s*([^,\s]+(?:\s+[^,\s=]+)*)")


def _parse_kv_blob(blob: str) -> dict[str, str]:
    out: dict[str, str] = {}
    for match in _KV_RX.finditer(blob):
        out[match.group(1).lower()] = match.group(2).strip()
    return out


def parse_cross_repository_product_evolution_intelligence_intent(raw: str) -> dict[str, Any] | None:
    text = str(raw or "").strip()
    if not text:
        return None

    if _VIEW_RX.match(text):
        return {"action": "view"}

    decision_match = _DECISION_RX.match(text)
    if decision_match:
        decision = decision_match.group("decision").lower()
        body = (decision_match.group("body") or "").strip()
        if not body:
            return None
        return {
            "action": "record",
            "kind": f"human_evolution_decision_{decision}",
            "content": body,
        }

    for rx, kind in (
        (_FEATURE_RX, "feature_evolution_note"),
        (_QUALITY_RX, "quality_evolution_note"),
        (_ARCH_RX, "architecture_evolution_note"),
        (_OPS_RX, "operational_evolution_note"),
        (_UX_RX, "ux_evolution_note"),
        (_GRAPH_RX, "opportunity_graph_note"),
        (_BACKLOG_RX, "evolution_backlog_note"),
    ):
        match = rx.match(text)
        if match:
            kv = _parse_kv_blob(match.group(1))
            return {
                "action": "record",
                "kind": kind,
                "content": match.group(1).strip(),
                "repository": kv.get("repository") or kv.get("repo"),
                "domain": kv.get("domain"),
                "target_repository": kv.get("target"),
                "opportunity_id": kv.get("opportunity") or kv.get("opportunity_id"),
            }

    lowered = text.lower()
    if lowered.startswith("product evolution intelligence:") or lowered.startswith(
        "portfolio evolution:"
    ):
        body = text.split(":", 1)[1].strip()
        return {
            "action": "record",
            "kind": "cross_repository_product_evolution_intelligence_record",
            "content": body,
        }

    return None


def handle_cross_repository_product_evolution_intelligence_intent(
    intent: dict[str, Any],
    *,
    session_id: str | None = None,
) -> dict[str, Any]:
    action = intent.get("action")
    if action == "view":
        return {"action": "view"}

    if action == "record":
        kind = str(intent.get("kind") or "")
        if kind not in CROSS_REPOSITORY_PRODUCT_EVOLUTION_INTELLIGENCE_RECORD_KINDS:
            raise ValueError(f"unsupported record kind: {kind!r}")
        repo = intent.get("repository")
        if repo and str(repo) not in PORTFOLIO_REPOSITORIES:
            raise ValueError(f"unsupported repository: {repo!r}")
        record = append_cross_repository_product_evolution_intelligence_record(
            kind=kind,
            content=str(intent.get("content") or ""),
            session_id=session_id,
            repository=str(repo) if repo else None,
            domain=str(intent.get("domain") or "") or None,
            target_repository=str(intent.get("target_repository") or "") or None,
            opportunity_id=str(intent.get("opportunity_id") or "") or None,
        )
        return {"action": "record", "record": record}

    raise ValueError(f"unsupported intent action: {action!r}")

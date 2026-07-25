# SPDX-License-Identifier: Apache-2.0
"""FIX 240 — chat intent for repository knowledge graph."""

from __future__ import annotations

import re
from typing import Any

_VIEW_RX = re.compile(
    r"\b("
    r"show\s+(?:repository\s+)?(?:knowledge\s+graph|engineering\s+intelligence)"
    r"|engineering\s+intelligence\s+dashboard"
    r"|repository\s+knowledge\s+graph"
    r"|change\s+impact\s+assessment"
    r")\b",
    re.I,
)

_ARCH_RX = re.compile(
    r"^\s*architecture\s+discovery\s*:\s*(?P<body>.+)$",
    re.I | re.S,
)

_DEP_RX = re.compile(
    r"^\s*dependency\s+mapping\s*:\s*(?P<body>.+)$",
    re.I | re.S,
)

_OWN_RX = re.compile(
    r"^\s*ownership\s+record\s*:\s*(?P<body>.+)$",
    re.I | re.S,
)

_HIST_RX = re.compile(
    r"^\s*historical\s+pattern\s*:\s*(?P<body>.+)$",
    re.I | re.S,
)

_IMPACT_RX = re.compile(
    r"^\s*change\s+impact\s+annotation\s*:\s*(?P<body>.+)$",
    re.I | re.S,
)

_FORBIDDEN_RX = re.compile(
    r"\b("
    r"generate\s+patch"
    r"|create\s+pr"
    r"|autonomous\s+merge"
    r"|modify\s+code"
    r"|deploy\s+now"
    r")\b",
    re.I,
)

_SUBSYSTEM_RX = re.compile(r"\bsubsystem\s*=\s*([^\s]+)", re.I)
_TEAM_RX = re.compile(r"\bteam\s*=\s*([^\s,]+)", re.I)
_SOURCE_RX = re.compile(r"\bsource\s*=\s*([^\s]+)", re.I)
_TARGET_RX = re.compile(r"\btarget\s*=\s*([^\s]+)", re.I)
_TYPE_RX = re.compile(r"\btype\s*=\s*(internal|external)", re.I)


def _parse_dependency_metadata(text: str) -> dict[str, Any]:
    meta: dict[str, Any] = {}
    source = _SOURCE_RX.search(text or "")
    target = _TARGET_RX.search(text or "")
    dep_type = _TYPE_RX.search(text or "")
    if source:
        meta["source"] = source.group(1).strip()
    if target:
        meta["target"] = target.group(1).strip()
    if dep_type:
        meta["dependency_type"] = dep_type.group(1).lower()
    return meta


def _parse_ownership_metadata(text: str) -> dict[str, Any]:
    meta: dict[str, Any] = {}
    subsystem = _SUBSYSTEM_RX.search(text or "")
    team = _TEAM_RX.search(text or "")
    if subsystem:
        meta["subsystem"] = subsystem.group(1).strip()
    if team:
        meta["team"] = team.group(1).strip()
        meta["role"] = "maintainer"
    return meta


def is_repository_knowledge_graph_intent(text: str) -> bool:
    raw = (text or "").strip()
    if not raw:
        return False
    if _FORBIDDEN_RX.search(raw):
        return False
    return bool(
        _VIEW_RX.search(raw)
        or _ARCH_RX.match(raw)
        or _DEP_RX.match(raw)
        or _OWN_RX.match(raw)
        or _HIST_RX.match(raw)
        or _IMPACT_RX.match(raw)
    )


def parse_repository_knowledge_graph_record_intent(
    text: str,
) -> tuple[str, str, dict[str, Any]] | None:
    raw = (text or "").strip()

    parsers = (
        (_ARCH_RX, "architecture_discovery_note", lambda body: {}),
        (_DEP_RX, "dependency_mapping_note", _parse_dependency_metadata),
        (_OWN_RX, "ownership_record_note", _parse_ownership_metadata),
        (_HIST_RX, "historical_pattern_note", lambda body: {}),
        (_IMPACT_RX, "change_impact_annotation", lambda body: {}),
    )
    for pattern, kind, meta_fn in parsers:
        match = pattern.match(raw)
        if match:
            body = (match.group("body") or "").strip()
            if body:
                return kind, body, meta_fn(body)
    return None

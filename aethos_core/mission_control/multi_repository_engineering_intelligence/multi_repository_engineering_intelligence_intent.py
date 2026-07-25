# SPDX-License-Identifier: Apache-2.0
"""FIX 260 — multi-repository engineering intelligence intent."""

from __future__ import annotations

import re
from typing import Any

from aethos_core.mission_control.multi_repository_engineering_intelligence.multi_repository_engineering_intelligence_contract import (
    MULTI_REPOSITORY_ENGINEERING_INTELLIGENCE_RECORD_KINDS,
    PORTFOLIO_REPOSITORIES,
)
from aethos_core.mission_control.multi_repository_engineering_intelligence.multi_repository_engineering_intelligence_store import (
    append_multi_repository_engineering_intelligence_record,
)

_VIEW_RX = re.compile(
    r"^\s*(?:show\s+)?(?:multi[-\s]?repo(?:sitory)?\s+engineering\s+intelligence|"
    r"portfolio\s+engineering\s+(?:dashboard|intelligence)|"
    r"multi[-\s]?repository\s+engineering\s+intelligence)\s*$",
    re.IGNORECASE,
)

_PORTFOLIO_RX = re.compile(
    r"^\s*show\s+portfolio\s+engineering\s+dashboard\s*$",
    re.IGNORECASE,
)

_CROSS_REPO_RX = re.compile(
    r"^\s*cross[-\s]?repo(?:sitory)?\s+dependency\s*:\s*(.+)$",
    re.IGNORECASE,
)

_PROGRAM_RX = re.compile(
    r"^\s*program\s+delivery\s+note\s*:\s*(.+)$",
    re.IGNORECASE,
)

_HEALTH_RX = re.compile(
    r"^\s*engineering\s+health\s+note\s*:\s*(.+)$",
    re.IGNORECASE,
)

_PORTFOLIO_OBS_RX = re.compile(
    r"^\s*portfolio\s+observation\s*:\s*(.+)$",
    re.IGNORECASE,
)

_KV_RX = re.compile(r"(\w+)\s*=\s*([^,\s]+(?:\s+[^,\s=]+)*)")


def _parse_kv_blob(blob: str) -> dict[str, str]:
    out: dict[str, str] = {}
    for match in _KV_RX.finditer(blob):
        out[match.group(1).lower()] = match.group(2).strip()
    return out


def parse_multi_repository_engineering_intelligence_intent(raw: str) -> dict[str, Any] | None:
    text = str(raw or "").strip()
    if not text:
        return None

    if _VIEW_RX.match(text) or _PORTFOLIO_RX.match(text):
        return {"action": "view"}

    match = _CROSS_REPO_RX.match(text)
    if match:
        kv = _parse_kv_blob(match.group(1))
        return {
            "action": "record",
            "kind": "cross_repo_dependency_note",
            "content": match.group(1).strip(),
            "source_repository": kv.get("source"),
            "target_repository": kv.get("target"),
            "relationship": kv.get("relationship") or kv.get("type") or "advisory",
        }

    match = _PROGRAM_RX.match(text)
    if match:
        return {
            "action": "record",
            "kind": "program_delivery_note",
            "content": match.group(1).strip(),
        }

    match = _HEALTH_RX.match(text)
    if match:
        kv = _parse_kv_blob(match.group(1))
        return {
            "action": "record",
            "kind": "engineering_health_note",
            "content": match.group(1).strip(),
            "repository": kv.get("repository") or kv.get("repo"),
        }

    match = _PORTFOLIO_OBS_RX.match(text)
    if match:
        return {
            "action": "record",
            "kind": "portfolio_observation_note",
            "content": match.group(1).strip(),
        }

    lowered = text.lower()
    if lowered.startswith("multi repo intelligence:") or lowered.startswith(
        "multi repository intelligence:"
    ):
        body = text.split(":", 1)[1].strip()
        return {
            "action": "record",
            "kind": "multi_repository_intelligence_record",
            "content": body,
        }

    return None


def handle_multi_repository_engineering_intelligence_intent(
    intent: dict[str, Any],
    *,
    session_id: str | None = None,
) -> dict[str, Any]:
    action = intent.get("action")
    if action == "view":
        return {"action": "view"}

    if action == "record":
        kind = str(intent.get("kind") or "")
        if kind not in MULTI_REPOSITORY_ENGINEERING_INTELLIGENCE_RECORD_KINDS:
            raise ValueError(f"unsupported record kind: {kind!r}")
        repo = intent.get("repository")
        if repo and str(repo) not in PORTFOLIO_REPOSITORIES:
            raise ValueError(f"unsupported repository: {repo!r}")
        record = append_multi_repository_engineering_intelligence_record(
            kind=kind,
            content=str(intent.get("content") or ""),
            session_id=session_id,
            repository=str(repo) if repo else None,
            source_repository=str(intent.get("source_repository") or "") or None,
            target_repository=str(intent.get("target_repository") or "") or None,
            relationship=str(intent.get("relationship") or "") or None,
        )
        return {"action": "record", "record": record}

    raise ValueError(f"unsupported intent action: {action!r}")

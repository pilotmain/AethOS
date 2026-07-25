# SPDX-License-Identifier: Apache-2.0
"""Research artifact storage."""

from __future__ import annotations

import json
import os
import stat
from pathlib import Path
from time import time
from typing import Any
from uuid import uuid4

from aethos_core.config import get_settings

ARTIFACT_TYPES = frozenset(
    {
        "web_intelligence_summary",
        "website_metadata_summary",
        "web_search_result_set",
        "research_policy_denial",
        "research_query",
        "research_result_set",
        "research_synthesis",
        "research_synthesis_engineering",
        "research_confidence_analysis",
        "research_contradiction_report",
        "research_browser_verification",
        "research_replay",
    }
)


def research_artifacts_root() -> Path:
    return Path(get_settings().research_artifacts_dir)


def new_artifact_id() -> str:
    return f"rart-{uuid4().hex[:12]}"


def store_research_artifact(
    *,
    artifact_type: str,
    intent: str,
    payload: dict[str, Any],
    channel: str = "chat",
    confidence: str = "medium",
    artifact_id: str | None = None,
) -> dict[str, Any]:
    if artifact_type not in ARTIFACT_TYPES:
        raise ValueError(f"Unknown research artifact type: {artifact_type}")
    aid = artifact_id or new_artifact_id()
    record = {
        "artifact_id": aid,
        "artifact_type": artifact_type,
        "intent": intent,
        "source_url": payload.get("source_url"),
        "evidence_source": payload.get("evidence_source"),
        "channel": channel,
        "confidence": confidence,
        "created_at": time(),
        "payload": payload,
    }
    root = research_artifacts_root()
    root.mkdir(parents=True, exist_ok=True)
    path = root / f"{aid}.json"
    path.write_text(json.dumps(record, indent=2), encoding="utf-8")
    os.chmod(path, stat.S_IRUSR | stat.S_IWUSR)
    _update_index(record)
    return record


def get_research_artifact(artifact_id: str) -> dict[str, Any] | None:
    path = research_artifacts_root() / f"{artifact_id}.json"
    if not path.is_file():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None


def list_research_artifacts(*, limit: int = 30, artifact_type: str | None = None) -> list[dict[str, Any]]:
    index_path = research_artifacts_root() / "index.json"
    if not index_path.is_file():
        return []
    try:
        ids = json.loads(index_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return []
    rows: list[dict[str, Any]] = []
    for aid in ids:
        if len(rows) >= limit:
            break
        path = research_artifacts_root() / f"{aid}.json"
        if path.is_file():
            try:
                row = json.loads(path.read_text(encoding="utf-8"))
            except (OSError, json.JSONDecodeError):
                continue
            if artifact_type and row.get("artifact_type") != artifact_type:
                continue
            rows.append(row)
    return rows


def _update_index(record: dict[str, Any]) -> None:
    index_path = research_artifacts_root() / "index.json"
    ids: list[str] = []
    if index_path.is_file():
        try:
            ids = json.loads(index_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            ids = []
    aid = record["artifact_id"]
    if aid in ids:
        ids.remove(aid)
    ids.insert(0, aid)
    index_path.write_text(json.dumps(ids[:200], indent=2), encoding="utf-8")


def clear_research_artifacts_for_tests() -> None:
    root = research_artifacts_root()
    if root.is_dir():
        for p in root.glob("*.json"):
            p.unlink()

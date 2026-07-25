# SPDX-License-Identifier: Apache-2.0
"""Browser evidence artifact storage — data/browser_artifacts/."""

from __future__ import annotations

import json
import os
import stat
from pathlib import Path
from time import time
from typing import Any
from uuid import uuid4

ARTIFACT_TYPES = frozenset(
    {
        "browser_screenshot",
        "browser_dom_snapshot",
        "browser_console_logs",
        "browser_network_summary",
        "browser_page_metadata",
        "browser_policy_denial",
        "deployment_url_resolution",
        "deployment_metadata_only",
    }
)


def artifacts_root() -> Path:
    from aethos_core.config import get_settings

    raw = Path(get_settings().browser_artifacts_dir)
    if raw.is_absolute():
        root = raw
    else:
        repo_root = Path(__file__).resolve().parents[3]
        root = repo_root / raw
    root = root.resolve()
    root.mkdir(parents=True, exist_ok=True)
    return root


def artifact_file_api_path(artifact_id: str) -> str:
    return f"/api/v1/browser/artifacts/{artifact_id}/file"


def enrich_artifact_record(meta: dict[str, Any]) -> dict[str, Any]:
    out = dict(meta)
    path = artifact_file_path(out)
    exists = bool(path and path.is_file())
    size = path.stat().st_size if exists and path else 0
    out["file_exists"] = exists
    out["file_size_bytes"] = size
    out["artifact_file_url"] = artifact_file_api_path(str(out.get("artifact_id") or ""))
    if path and exists:
        out["file_path"] = str(path)
    out["file_http_status"] = 200 if exists and size > 0 else 404
    return out


def _subdir(name: str) -> Path:
    path = artifacts_root() / name
    path.mkdir(parents=True, exist_ok=True)
    return path


def new_artifact_id() -> str:
    return f"bart-{uuid4().hex[:12]}"


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    os.chmod(tmp, stat.S_IRUSR | stat.S_IWUSR)
    tmp.replace(path)


def store_artifact(
    *,
    capture_type: str,
    source_url: str,
    session_id: str,
    headless: bool,
    approved: bool,
    risk_tier: str,
    payload: dict[str, Any],
    binary: bytes | None = None,
    artifact_type: str,
) -> dict[str, Any]:
    artifact_id = new_artifact_id()
    created_at = time()
    meta: dict[str, Any] = {
        "artifact_id": artifact_id,
        "provider": "browser_runtime",
        "created_at": created_at,
        "session_id": session_id,
        "source_url": source_url,
        "capture_type": capture_type,
        "artifact_type": artifact_type,
        "headless": headless,
        "approved": approved,
        "risk_tier": risk_tier,
        **payload,
    }

    if artifact_type == "browser_screenshot" and binary:
        rel = Path("screenshots") / f"{artifact_id}.png"
        path = artifacts_root() / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(binary)
        os.chmod(path, stat.S_IRUSR | stat.S_IWUSR)
        if not path.is_file() or path.stat().st_size <= 0:
            raise RuntimeError("Screenshot file was not written successfully.")
        meta["file_path"] = str(rel)
        meta["media_type"] = "image/png"
    elif artifact_type == "browser_dom_snapshot":
        rel = Path("dom") / f"{artifact_id}.json"
        _write_json(artifacts_root() / rel, payload.get("dom") or {})
        meta["file_path"] = str(rel)
    elif artifact_type == "browser_console_logs":
        rel = Path("console") / f"{artifact_id}.json"
        _write_json(artifacts_root() / rel, {"logs": payload.get("logs") or []})
        meta["file_path"] = str(rel)
    elif artifact_type == "browser_network_summary":
        rel = Path("network") / f"{artifact_id}.json"
        _write_json(artifacts_root() / rel, {"failures": payload.get("failures") or []})
        meta["file_path"] = str(rel)
    elif artifact_type == "browser_page_metadata":
        rel = Path("metadata") / f"{artifact_id}.json"
        _write_json(artifacts_root() / rel, payload.get("metadata") or {})
        meta["file_path"] = str(rel)
    elif artifact_type == "browser_policy_denial":
        rel = Path("metadata") / f"{artifact_id}-denial.json"
        _write_json(artifacts_root() / rel, payload)
        meta["file_path"] = str(rel)
    elif artifact_type in ("deployment_url_resolution", "deployment_metadata_only"):
        rel = Path("metadata") / f"{artifact_id}.json"
        body = payload.get("resolution") or payload.get("metadata") or payload
        _write_json(artifacts_root() / rel, body if isinstance(body, dict) else {"payload": body})
        meta["file_path"] = str(rel)

    index_path = artifacts_root() / "index.json"
    index: list[dict[str, Any]] = []
    if index_path.is_file():
        try:
            raw_index = json.loads(index_path.read_text(encoding="utf-8"))
            if isinstance(raw_index, dict):
                index = list(raw_index.get("artifacts") or [])
            elif isinstance(raw_index, list):
                index = raw_index
        except json.JSONDecodeError:
            index = []
    index.insert(0, {k: meta[k] for k in meta if k != "dom"})
    index = index[:500]
    _write_json(index_path, {"artifacts": index})
    return enrich_artifact_record(meta)


def list_artifacts(*, limit: int = 50) -> list[dict[str, Any]]:
    index_path = artifacts_root() / "index.json"
    if not index_path.is_file():
        return []
    try:
        raw = json.loads(index_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return []
    items = raw.get("artifacts") or []
    return [enrich_artifact_record(row) for row in items[:limit]]


def get_artifact(artifact_id: str) -> dict[str, Any] | None:
    for row in list_artifacts(limit=500):
        if row.get("artifact_id") == artifact_id:
            return enrich_artifact_record(row)
    return None


def artifact_file_path(meta: dict[str, Any]) -> Path | None:
    rel = meta.get("file_path")
    if not rel:
        return None
    return artifacts_root() / str(rel)

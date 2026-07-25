# SPDX-License-Identifier: Apache-2.0
"""Browser evidence audit — no secrets."""

from __future__ import annotations

import json
import logging
from pathlib import Path
from time import time
from typing import Any

_log = logging.getLogger(__name__)


def _audit_path() -> Path:
    from aethos_core.browser.runtime.browser_artifacts import artifacts_root

    return artifacts_root() / "browser_audit.jsonl"


def append_browser_audit_event(
    *,
    action: str,
    target_url: str | None = None,
    capture_type: str | None = None,
    policy_tier: str | None = None,
    approved: bool = False,
    result: str = "unknown",
    session_id: str | None = None,
    artifact_ids: list[str] | None = None,
    detail: str | None = None,
) -> None:
    row: dict[str, Any] = {
        "at": time(),
        "action": action,
        "operator": "human",
        "approved": approved,
        "result": result,
    }
    if target_url:
        row["target_url"] = target_url[:500]
    if capture_type:
        row["capture_type"] = capture_type
    if policy_tier:
        row["policy_tier"] = policy_tier
    if session_id:
        row["session_id"] = session_id
    if artifact_ids:
        row["artifact_ids"] = artifact_ids[:20]
    if detail:
        row["detail"] = detail[:240]
    try:
        path = _audit_path()
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("a", encoding="utf-8") as fh:
            fh.write(json.dumps(row) + "\n")
    except OSError:
        _log.exception("browser_audit_write_failed")
    _log.info(
        "browser_audit action=%s url=%s result=%s tier=%s",
        action,
        target_url or "—",
        result,
        policy_tier or "—",
    )

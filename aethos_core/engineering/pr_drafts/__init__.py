# SPDX-License-Identifier: Apache-2.0
"""PR draft storage and formatting."""

from __future__ import annotations

import json
from pathlib import Path
from time import time
from typing import Any
from uuid import uuid4

from aethos_core.agents.runtime.paths import agent_artifacts_root
from aethos_core.engineering.pr_generation import format_pr_body, generate_pr_draft


def _root() -> Path:
    return agent_artifacts_root() / "engineering_pr_drafts"


def store_pr_draft(*, preflight_id: str, draft: dict[str, Any]) -> dict[str, Any]:
    draft_id = f"eprd-{uuid4().hex[:12]}"
    record = {"draft_id": draft_id, "preflight_id": preflight_id, "created_at": time(), **draft}
    root = _root()
    root.mkdir(parents=True, exist_ok=True)
    (root / f"{draft_id}.json").write_text(json.dumps(record, indent=2), encoding="utf-8")
    return record


def clear_pr_drafts_for_tests() -> None:
    root = _root()
    if root.is_dir():
        for p in root.glob("*.json"):
            p.unlink()


def list_pr_drafts(*, limit: int = 20) -> list[dict[str, Any]]:
    root = _root()
    if not root.is_dir():
        return []
    rows: list[dict[str, Any]] = []
    for path in sorted(root.glob("*.json"), key=lambda p: p.stat().st_mtime, reverse=True):
        try:
            rows.append(json.loads(path.read_text(encoding="utf-8")))
        except (OSError, json.JSONDecodeError):
            continue
        if len(rows) >= limit:
            break
    return rows


def build_governed_pr_draft(
    *,
    preflight: dict[str, Any],
    execution: dict[str, Any] | None,
    diff_intel: dict[str, Any] | None = None,
    research_context: dict[str, Any] | None = None,
) -> dict[str, Any]:
    draft = generate_pr_draft(preflight=preflight, execution=execution)
    intel = diff_intel or {}
    body_extra = [
        "",
        "### Diff intelligence",
        f"- Severity: **{intel.get('severity', 'low')}**",
        f"- Migration risk: {intel.get('migration_risk', 'low')}",
        f"- API contract changes: {intel.get('api_contract_changes', False)}",
    ]
    if intel.get("warnings"):
        body_extra.append("**Warnings:**")
        for w in intel["warnings"][:5]:
            body_extra.append(f"- {w}")
    if research_context:
        body_extra.extend(
            [
                "",
                "### Research evidence",
                f"- Replay: `{research_context.get('replay_id', '—')}`",
            ]
        )
    draft["body"] = (draft.get("body") or "") + "\n".join(body_extra)
    draft["diff_intelligence"] = intel
    draft["governance_statement"] = "Human merge required — auto-merge disabled."
    draft["merge_enabled"] = False
    draft["auto_merge"] = False
    return draft

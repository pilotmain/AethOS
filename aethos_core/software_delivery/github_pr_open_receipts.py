# SPDX-License-Identifier: Apache-2.0
"""FIX 125I — GitHub PR open receipts."""

from __future__ import annotations

import json
import uuid
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from aethos_core.software_delivery.github_pr_open_contract import GITHUB_PR_OPEN_SCHEMA_VERSION

_RECEIPTS: dict[str, list[dict[str, Any]]] = {}


def _store_dir() -> Path:
    root = Path(__file__).resolve().parents[2] / "data" / "software_delivery_github_pr_open_receipts"
    root.mkdir(parents=True, exist_ok=True)
    return root


def _path(plan_id: str) -> Path:
    safe = (plan_id or "").strip().replace("/", "_")[:128]
    return _store_dir() / f"{safe}_github_pr_open_receipts.json"


def clear_for_tests() -> None:
    from aethos_core.software_delivery.test_data_guard import tests_may_clear_persisted_data

    if not tests_may_clear_persisted_data():
        return
    _RECEIPTS.clear()
    if _store_dir().exists():
        for child in _store_dir().glob("*_github_pr_open_receipts.json"):
            child.unlink(missing_ok=True)


def list_github_pr_open_receipts(*, plan_id: str) -> list[dict[str, Any]]:
    if plan_id in _RECEIPTS:
        return list(_RECEIPTS[plan_id])
    path = _path(plan_id)
    if not path.is_file():
        return []
    try:
        rows = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return []
    if isinstance(rows, list):
        _RECEIPTS[plan_id] = list(rows)
        return list(rows)
    return []


def record_github_pr_open_receipt(
    *,
    plan_id: str,
    phase: str,
    status: str = "pr_open_success",
    detail: str = "",
    pr_open_id: str = "",
    pr_url: str = "",
    blockers: list[str] | None = None,
) -> dict[str, Any]:
    receipt = {
        "receipt_id": f"sgpr-{uuid.uuid4().hex[:12]}",
        "plan_id": plan_id,
        "pr_open_id": pr_open_id,
        "phase": phase,
        "status": status,
        "detail": detail,
        "pr_url": pr_url,
        "blockers": list(blockers or []),
        "merge_performed": False,
        "human_review_required": True,
        "schema_version": GITHUB_PR_OPEN_SCHEMA_VERSION,
        "recorded_at": datetime.now(UTC).isoformat(),
    }
    rows = list_github_pr_open_receipts(plan_id=plan_id)
    rows.append(receipt)
    _RECEIPTS[plan_id] = rows
    _path(plan_id).write_text(json.dumps(rows, indent=2), encoding="utf-8")
    return receipt

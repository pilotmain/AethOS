# SPDX-License-Identifier: Apache-2.0
"""Audit attribution — who approved/executed."""

from __future__ import annotations

import json
from time import time
from typing import Any
from uuid import uuid4

from aethos_core.orgs.paths import orgs_root


def _path():
    return orgs_root() / "audit_attribution.jsonl"


def record_attribution(
    *,
    actor_id: str,
    actor_role: str,
    action: str,
    resource_type: str,
    resource_id: str,
    org_id: str | None = None,
    approved: bool = False,
) -> dict[str, Any]:
    record = {
        "attribution_id": f"attr-{uuid4().hex[:10]}",
        "at": time(),
        "actor_id": actor_id,
        "actor_role": actor_role,
        "action": action,
        "resource_type": resource_type,
        "resource_id": resource_id,
        "org_id": org_id,
        "approved": approved,
        "immutable": True,
    }
    path = _path()
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(record) + "\n")
    return record


def list_attributions(*, limit: int = 50) -> list[dict[str, Any]]:
    path = _path()
    if not path.is_file():
        return []
    lines = path.read_text(encoding="utf-8").strip().splitlines()
    rows: list[dict[str, Any]] = []
    for line in reversed(lines[-limit:]):
        try:
            rows.append(json.loads(line))
        except json.JSONDecodeError:
            continue
    return rows


def clear_attributions_for_tests() -> None:
    path = _path()
    if path.is_file():
        path.unlink()

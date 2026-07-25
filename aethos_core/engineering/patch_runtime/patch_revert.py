# SPDX-License-Identifier: Apache-2.0
"""Patch revert — restore sandbox from rollback snapshot."""

from __future__ import annotations

import shutil
from pathlib import Path
from typing import Any

from aethos_core.engineering.governance.engineering_rollback import get_rollback_snapshot


def revert_workspace_from_snapshot(snapshot_id: str) -> dict[str, Any]:
    snap = get_rollback_snapshot(snapshot_id)
    if not snap:
        return {"ok": False, "error": "snapshot_not_found"}
    backup = snap.get("sandbox_backup")
    sandbox_path = snap.get("sandbox_path")
    if not backup or not sandbox_path:
        return {"ok": False, "error": "no_sandbox_backup", "snapshot_id": snapshot_id}
    src = Path(str(backup))
    dest = Path(str(sandbox_path))
    if not src.is_dir():
        return {"ok": False, "error": "backup_missing"}
    if dest.is_dir():
        shutil.rmtree(dest)
    shutil.copytree(src, dest)
    return {"ok": True, "snapshot_id": snapshot_id, "restored_to": str(dest)}

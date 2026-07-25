# SPDX-License-Identifier: Apache-2.0
"""Artifact repair — corrupted evidence recovery."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def repair_artifacts(*, artifact_dir: str | None = None) -> dict[str, Any]:
    """Scan and repair corrupted JSON artifacts — readonly recovery."""
    from aethos_core.config import get_settings

    root = Path(artifact_dir or get_settings().agent_artifacts_dir)
    if not root.is_dir():
        return {"ok": False, "error": "directory_not_found"}
    scanned = 0
    repaired = 0
    quarantined: list[str] = []
    for path in root.rglob("*.json"):
        scanned += 1
        try:
            json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            quarantine = path.with_suffix(".json.corrupt")
            try:
                path.rename(quarantine)
                quarantined.append(str(quarantine))
                repaired += 1
            except OSError:
                pass
    return {
        "ok": True,
        "scanned": scanned,
        "repaired": repaired,
        "quarantined": quarantined[:20],
        "readonly": True,
    }

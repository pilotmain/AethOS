# SPDX-License-Identifier: Apache-2.0
"""Agent artifact paths."""

from __future__ import annotations

from pathlib import Path


def agent_artifacts_root() -> Path:
    from aethos_core.config import get_settings

    raw = Path(get_settings().agent_artifacts_dir)
    if raw.is_absolute():
        root = raw
    else:
        root = Path(__file__).resolve().parents[3] / raw
    root = root.resolve()
    root.mkdir(parents=True, exist_ok=True)
    return root

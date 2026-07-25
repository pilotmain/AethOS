# SPDX-License-Identifier: Apache-2.0
"""Config migration assistant — .env evolution guidance."""

from __future__ import annotations

from pathlib import Path
from typing import Any

_NEW_KEYS_99 = [
    "DEPLOYMENT_MODE",
    "WORKER_MODE",
    "EDGE_RUNTIME_ENABLED",
    "HOSTED_CLOUD_ENABLED",
]


def analyze_env_migration() -> dict[str, Any]:
    """Suggest .env migrations — no secrets."""
    example = Path(".env.example")
    env = Path(".env")
    example_keys: set[str] = set()
    env_keys: set[str] = set()
    if example.is_file():
        for line in example.read_text(encoding="utf-8").splitlines():
            if "=" in line and not line.strip().startswith("#"):
                example_keys.add(line.split("=", 1)[0].strip())
    if env.is_file():
        for line in env.read_text(encoding="utf-8").splitlines():
            if "=" in line and not line.strip().startswith("#"):
                env_keys.add(line.split("=", 1)[0].strip())
    missing_new = [k for k in _NEW_KEYS_99 if k not in env_keys]
    return {
        "ok": True,
        "missing_new_keys": missing_new,
        "restart_required": bool(missing_new),
        "guidance": "Add missing keys from .env.example and restart API + workers.",
    }

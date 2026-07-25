# SPDX-License-Identifier: Apache-2.0
"""Canonical paths for local workspace intelligence."""

from __future__ import annotations

from pathlib import Path

_INDEX_FILENAME = "workspaces.json"
_REGISTRY_DIRNAME = "local_workspace"
_ARTIFACTS_DIRNAME = "local_workspace_artifacts"
_MEMORY_FILENAME = "engineering_memory.json"


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


def registry_root() -> Path:
    from aethos_core.config import get_settings

    raw = Path(get_settings().local_workspace_registry_dir)
    if raw.is_absolute():
        root = raw
    else:
        root = _repo_root() / raw
    root = root.resolve()
    root.mkdir(parents=True, exist_ok=True)
    return root


def workspaces_index_path() -> Path:
    return registry_root() / _INDEX_FILENAME


def artifacts_root() -> Path:
    from aethos_core.config import get_settings

    raw = Path(get_settings().local_workspace_artifacts_dir)
    if raw.is_absolute():
        root = raw
    else:
        root = _repo_root() / raw
    root = root.resolve()
    root.mkdir(parents=True, exist_ok=True)
    return root


def engineering_memory_path() -> Path:
    return registry_root() / _MEMORY_FILENAME

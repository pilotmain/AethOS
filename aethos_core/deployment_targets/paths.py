# SPDX-License-Identifier: Apache-2.0
"""Canonical paths for deployment target registry."""

from __future__ import annotations

from pathlib import Path

_TARGETS_FILENAME = "targets.json"
_BINDINGS_FILENAME = "bindings.json"
_REGISTRY_DIRNAME = "deployment_targets"


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


def registry_root() -> Path:
    from aethos_core.config import get_settings

    raw = Path(get_settings().deployment_targets_registry_dir)
    if raw.is_absolute():
        root = raw
    else:
        root = _repo_root() / raw
    root = root.resolve()
    root.mkdir(parents=True, exist_ok=True)
    return root


def targets_index_path() -> Path:
    return registry_root() / _TARGETS_FILENAME


def bindings_index_path() -> Path:
    return registry_root() / _BINDINGS_FILENAME


def session_deploy_targets_path() -> Path:
    return registry_root() / "session_deploy_targets.json"

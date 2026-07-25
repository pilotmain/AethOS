# SPDX-License-Identifier: Apache-2.0
"""Workspace runtime paths."""

from __future__ import annotations

from pathlib import Path


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


def workspace_artifacts_root() -> Path:
    root = _repo_root() / "data" / "workspace_artifacts"
    root.mkdir(parents=True, exist_ok=True)
    return root


def workspace_runtime_root() -> Path:
    from aethos_core.agents.runtime.paths import agent_artifacts_root

    root = agent_artifacts_root() / "workspace_runtime"
    root.mkdir(parents=True, exist_ok=True)
    return root

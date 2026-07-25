# SPDX-License-Identifier: Apache-2.0
"""Presence memory paths."""

from __future__ import annotations

from pathlib import Path


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


def presence_memory_root() -> Path:
    root = _repo_root() / "data" / "presence_memory"
    root.mkdir(parents=True, exist_ok=True)
    return root


def presence_artifacts_root() -> Path:
    root = presence_memory_root() / "artifacts"
    root.mkdir(parents=True, exist_ok=True)
    return root

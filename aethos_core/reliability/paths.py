# SPDX-License-Identifier: Apache-2.0
"""Reliability artifact paths."""

from __future__ import annotations

from pathlib import Path


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


def reliability_root() -> Path:
    root = _repo_root() / "data" / "reliability"
    root.mkdir(parents=True, exist_ok=True)
    return root


def governance_memory_root() -> Path:
    root = reliability_root() / "governance_memory"
    root.mkdir(parents=True, exist_ok=True)
    return root

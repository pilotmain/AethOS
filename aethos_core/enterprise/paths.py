# SPDX-License-Identifier: Apache-2.0
"""Enterprise artifact paths."""

from __future__ import annotations

from pathlib import Path


def enterprise_root() -> Path:
    root = Path(__file__).resolve().parents[2] / "data" / "enterprise"
    root.mkdir(parents=True, exist_ok=True)
    return root


def demo_mode_root() -> Path:
    root = enterprise_root() / "demo_mode"
    root.mkdir(parents=True, exist_ok=True)
    return root

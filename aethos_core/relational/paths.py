# SPDX-License-Identifier: Apache-2.0
"""Relational intelligence paths."""

from __future__ import annotations

from pathlib import Path


def relational_root() -> Path:
    root = Path(__file__).resolve().parents[2] / "data" / "relational"
    root.mkdir(parents=True, exist_ok=True)
    return root

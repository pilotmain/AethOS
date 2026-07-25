# SPDX-License-Identifier: Apache-2.0
"""Production infrastructure paths."""

from __future__ import annotations

from pathlib import Path


def production_root() -> Path:
    root = Path(__file__).resolve().parents[2] / "data" / "production"
    root.mkdir(parents=True, exist_ok=True)
    return root

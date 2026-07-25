# SPDX-License-Identifier: Apache-2.0
"""Organization paths."""

from __future__ import annotations

from pathlib import Path


def orgs_root() -> Path:
    root = Path(__file__).resolve().parents[2] / "data" / "orgs"
    root.mkdir(parents=True, exist_ok=True)
    return root

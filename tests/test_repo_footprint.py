# SPDX-License-Identifier: Apache-2.0
"""Repo footprint metrics for §D3/D4 reporting."""

from __future__ import annotations

from pathlib import Path


def test_aethos_core_top_level_package_count_tracked():
    root = Path(__file__).resolve().parents[1] / "aethos_core"
    packages = [p.name for p in root.iterdir() if p.is_dir() and not p.name.startswith(".")]
    # Baseline ~265; diet waves should monotonically shrink this count.
    assert len(packages) < 300

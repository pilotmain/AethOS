# SPDX-License-Identifier: Apache-2.0
"""Legacy polish pipeline absence tracking (§D1/D2)."""

from __future__ import annotations

from pathlib import Path


def test_conversational_constellation_count_documented():
    root = Path(__file__).resolve().parents[1] / "aethos_core"
    conv = [p.name for p in root.iterdir() if p.is_dir() and p.name.startswith("conversational_")]
    assert len(conv) == 0


def test_legacy_route_lane_guard_removed():
    from pathlib import Path

    ownership = Path(__file__).resolve().parents[1] / "aethos_core" / "operational_cognition" / "route_ownership.py"
    assert not ownership.is_file()

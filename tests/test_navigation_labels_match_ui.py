# SPDX-License-Identifier: Apache-2.0
"""CI guard: every Mission Control navigation label the backend tells operators must be a
REAL, clickable label in the shipped UI (web/lib/missionControl/views.ts).

This makes "go to Mission Control → <button that doesn't exist>" impossible to ship — the
historical bug where chat said "Mission Control → Connections / Jobs / Approvals / Providers"
but the actual buttons are "Credential Center / Tracked Work / Approval Inbox".
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest

from aethos_core.mission_control.visible_navigation_registry import (
    CAPABILITY_TRUTH,
    OPERATOR_DESTINATIONS,
    REAL_OPERATOR_SURFACES,
)

# The rendered sidebar is Flat nav — these are the labels the operator actually clicks.
_VIEWS_TS = Path(__file__).resolve().parents[1] / "web" / "lib" / "missionControl" / "flatNavigation.ts"

# Real surfaces that are NOT Mission Control sidebar labels (top-nav tabs, files, expander).
_NON_MC_SURFACES = {
    "Canvas tab",
    ".env file",
    "the Research / Documents / Notes / Email / Calendar / Foundry tabs",
    "Advanced settings",  # the expander, not a leaf
}

# Deep view-id labels that are NOT the real clickable Flat-nav buttons — these confuse
# operators ("go to Approval Inbox" → there's no such button; it's "Approvals").
_FORBIDDEN_AFTER_MC = {
    "Connections",
    "Approval Inbox",
    "Tracked Work",
    "Credential Center",
    "Provider Inventory",
    "Channel Integration",
    "Local Workspaces",
    "Settings → Connections",
}


def _ui_labels() -> set[str]:
    """Real Flat-nav sidebar labels (primary groups + advanced sections)."""
    txt = _VIEWS_TS.read_text(encoding="utf-8")
    return set(re.findall(r'label:\s*"([^"]+)"', txt))


def _mc_leaf(surface: str) -> str:
    # last segment after "Mission Control → ... → X"
    return surface.split("→")[-1].strip()


@pytest.mark.skipif(not _VIEWS_TS.is_file(), reason="views.ts not present in this checkout")
def test_real_operator_surfaces_exist_in_ui():
    ui = _ui_labels()
    for surface in REAL_OPERATOR_SURFACES:
        if surface in _NON_MC_SURFACES:
            continue
        leaf = _mc_leaf(surface)
        assert leaf in ui, f"REAL_OPERATOR_SURFACES → {surface!r}: '{leaf}' is not a real UI label"


@pytest.mark.skipif(not _VIEWS_TS.is_file(), reason="views.ts not present in this checkout")
def test_operator_destinations_exist_in_ui():
    ui = _ui_labels()
    for key, surface in OPERATOR_DESTINATIONS.items():
        if surface in _NON_MC_SURFACES or not surface.startswith("Mission Control"):
            continue
        leaf = _mc_leaf(surface)
        assert leaf in ui, f"OPERATOR_DESTINATIONS[{key!r}] → {surface!r}: '{leaf}' is not a real UI label"


@pytest.mark.skipif(not _VIEWS_TS.is_file(), reason="views.ts not present in this checkout")
def test_capability_truth_surfaces_exist_in_ui():
    ui = _ui_labels()
    for cap_id, row in CAPABILITY_TRUTH.items():
        surface = row["surface"]
        if surface in _NON_MC_SURFACES or not surface.startswith("Mission Control"):
            continue
        leaf = _mc_leaf(surface)
        assert leaf in ui, f"capability {cap_id} → {surface!r}: '{leaf}' is not a real UI label"


def test_backend_never_uses_forbidden_mc_labels():
    """Scan aethos_core for the known-wrong 'Mission Control → <bad>' directions."""
    root = Path(__file__).resolve().parents[1] / "aethos_core"
    offenders: list[str] = []
    for py in root.rglob("*.py"):
        # The registry intentionally references some of these as keys to REWRITE them away.
        if py.name == "visible_navigation_registry.py":
            continue
        text = py.read_text(encoding="utf-8", errors="ignore")
        for bad in _FORBIDDEN_AFTER_MC:
            for pat in (f"Mission Control → {bad}", f"Mission Control → {bad}"):
                if pat in text:
                    offenders.append(f"{py.relative_to(root)} :: {pat}")
        if "Settings → Connections" in text:
            offenders.append(f"{py.relative_to(root)} :: Settings → Connections")
    assert not offenders, "Wrong MC navigation labels found:\n" + "\n".join(sorted(set(offenders)))

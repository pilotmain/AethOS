# SPDX-License-Identifier: Apache-2.0
"""The arbiter is labeled 'Arbiter' in the sidebar (flatNavigation.ts), but the agent and
tooling called it 'Multi-model arbiter' — so 'go to Mission Control → Multi-model arbiter'
sent users to a button that doesn't exist. Lock the directions to the real label.
"""

from __future__ import annotations

from pathlib import Path

from aethos_core.mission_control.visible_navigation_registry import (
    operator_surface,
    sanitize_operator_navigation_copy,
)

_ROOT = Path(__file__).resolve().parents[1]


def test_arbiter_destination_resolves_to_real_sidebar_label():
    assert operator_surface("arbiter") == "Mission Control → Arbiter"


def test_sanitizer_rewrites_multi_model_arbiter_nav_phrase():
    out = sanitize_operator_navigation_copy("Open Mission Control → Multi-model arbiter for detail.")
    assert "Mission Control → Arbiter" in out
    assert "Multi-model arbiter" not in out


def test_flatnav_has_arbiter_label():
    nav = (_ROOT / "web/lib/missionControl/flatNavigation.ts").read_text(encoding="utf-8")
    assert 'label: "Arbiter"' in nav


def test_no_agent_string_points_to_nonexistent_arbiter_path():
    for rel in (
        "aethos_core/execution_brain/agent_tool_executor.py",
        "aethos_core/execution_brain/agent_tool_catalog.py",
    ):
        src = (_ROOT / rel).read_text(encoding="utf-8")
        assert "Mission Control → Multi-model arbiter" not in src, rel
        assert "Mission Control → Multi-model\n" not in src, rel  # guard against line-wrapped split

# SPDX-License-Identifier: Apache-2.0
"""Proactive suggestions: surface ranked proposals from existing signals, gated off by
default, dismissable, and strictly read-only (proposals carry an action hint, never run)."""

from __future__ import annotations

from unittest.mock import patch
from uuid import uuid4

import aethos_core.proactive.suggestions as pro
from aethos_core.tenancy import tenant_scope


def _t() -> str:
    # Unique tenant per test → hermetic against the shared on-disk data store.
    return f"pro-{uuid4().hex}@example.com"


class _Settings:
    def __init__(self, enabled):
        self.proactive_suggestions_enabled = enabled


def _alert_obs():
    return [{"monitor_id": "mon-1", "monitor_name": "Prod API", "summary": "⚠ down", "alert": True}]


def test_disabled_returns_empty():
    with tenant_scope(_t()), patch.object(pro, "get_settings", return_value=_Settings(False)):
        assert pro.generate_suggestions() == []


def test_enabled_surfaces_monitor_alert_high_severity():
    with tenant_scope(_t()), \
         patch.object(pro, "get_settings", return_value=_Settings(True)), \
         patch("aethos_core.monitors.recent_observations", return_value=_alert_obs()), \
         patch.object(pro, "_from_failures", return_value=[]), \
         patch.object(pro, "_from_approvals", return_value=[]), \
         patch.object(pro, "_from_skills", return_value=[]):
        out = pro.generate_suggestions()
    assert len(out) == 1
    assert out[0]["severity"] == "high"
    assert out[0]["source"] == "monitor"
    assert "action_hint" in out[0] and out[0]["action_hint"]  # proposal, not an action


def test_dismiss_hides_suggestion():
    with tenant_scope(_t()), \
         patch.object(pro, "get_settings", return_value=_Settings(True)), \
         patch("aethos_core.monitors.recent_observations", return_value=_alert_obs()), \
         patch.object(pro, "_from_failures", return_value=[]), \
         patch.object(pro, "_from_approvals", return_value=[]), \
         patch.object(pro, "_from_skills", return_value=[]):
        first = pro.generate_suggestions()
        assert len(first) == 1
        pro.dismiss_suggestion(first[0]["id"])
        after = pro.generate_suggestions()
    assert after == []  # dismissed suggestions don't nag


def test_ranking_high_before_medium():
    with tenant_scope(_t()), \
         patch.object(pro, "get_settings", return_value=_Settings(True)), \
         patch.object(pro, "_from_monitors", return_value=[pro._suggest("monitor", "m", "M", "d", "high", "h")]), \
         patch.object(pro, "_from_failures", return_value=[pro._suggest("failure", "f", "F", "d", "medium", "h")]), \
         patch.object(pro, "_from_approvals", return_value=[]), \
         patch.object(pro, "_from_skills", return_value=[]):
        out = pro.generate_suggestions()
    assert [s["severity"] for s in out] == ["high", "medium"]

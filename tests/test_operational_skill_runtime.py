# SPDX-License-Identifier: Apache-2.0
"""Operational skill runtime bootstrap and registry tests."""

from __future__ import annotations

from aethos_core.operational_skill_runtime import bootstrap_operational_runtime, is_operational_runtime_ready
from aethos_core.operational_skill_runtime.operation_planner import plan_operation
from aethos_core.operational_skill_runtime.skill_loader import load_all_provider_skills, load_skill_markdown
from aethos_core.operational_skill_runtime.skill_registry import list_registered_providers, skill_registry_snapshot


def test_bootstrap_loads_identity_and_provider_skills():
    snapshot = bootstrap_operational_runtime(force=True)
    assert snapshot["ready"] is True
    assert is_operational_runtime_ready() is True
    assert snapshot["skills"]["loaded_count"] >= 6


def test_skill_markdown_loaded_for_railway():
    doc = load_skill_markdown("railway")
    assert doc["loaded"] is True
    assert "restart service" in doc["content"].lower()


def test_registry_lists_all_providers():
    providers = list_registered_providers()
    assert "railway" in providers
    assert "aws" in providers
    assert "vercel" in providers


def test_stub_provider_plan_fails_honestly():
    plan = plan_operation(provider="vercel", operation="redeploy", target={"service_name": "demo"})
    assert plan["ok"] is False


def test_registry_snapshot_marks_railway_implemented():
    snap = skill_registry_snapshot()
    railway = next(row for row in snap["providers"] if row["provider"] == "railway")
    assert railway["status"] == "implemented"
    vercel = next(row for row in snap["providers"] if row["provider"] == "vercel")
    # Vercel graduated from a pure stub to a partial implementation (real
    # discovery/plan/dry-run + governed redeploy execute), so "partial" is the
    # honest status now — read works, not every mutation does.
    assert vercel["status"] == "partial"


def test_load_all_provider_skills_includes_markdown():
    payload = load_all_provider_skills(force=True)
    assert payload["markdown_count"] >= 6

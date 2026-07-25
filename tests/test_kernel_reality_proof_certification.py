# SPDX-License-Identifier: Apache-2.0
"""KERNEL_REALITY_PROOF_001 certification."""

from __future__ import annotations

from unittest.mock import patch

import pytest

from aethos_core.execution_brain.conversation_plan_registry import clear_conversation_plans_for_tests
from aethos_core.observability.metrics import clear_metrics_for_tests, snapshot_metrics
from aethos_core.operational_session import clear_operational_sessions_for_tests
from aethos_core.operational_session.goal_completion_registry import (
    goal_completion_summary,
    load_goal_records,
    record_readonly_goal_completed,
)
from aethos_core.operational_session.kernel_reality_registry import (
    capture_kernel_reality_turn,
    classify_proof_category,
    clear_reality_registry_for_tests,
    compute_reality_summary,
    detect_provider_confusion,
    is_continuity_prompt,
    load_reality_records,
    provider_routing_summary,
    save_daily_snapshot,
    soak_progress,
)
from aethos_core.operational_session.kernel_router import route_operational_conversation_kernel_turn
from aethos_core.operational_session.provider_routing_proof import evaluate_provider_routing
from aethos_core.operational_session.session_subject import SessionSubject


@pytest.fixture(autouse=True)
def _clean():
    clear_reality_registry_for_tests()
    clear_operational_sessions_for_tests()
    clear_conversation_plans_for_tests()
    clear_metrics_for_tests()
    yield
    clear_reality_registry_for_tests()
    clear_operational_sessions_for_tests()
    clear_conversation_plans_for_tests()
    clear_metrics_for_tests()


@pytest.fixture
def enable_kernel(monkeypatch):
    from aethos_core.config import get_settings

    s = get_settings()
    monkeypatch.setattr(s, "operational_conversation_kernel_enabled", True)
    monkeypatch.setattr(s, "kernel_reality_capture_enabled", True)
    monkeypatch.setattr(s, "execution_brain_use_llm", False)
    monkeypatch.setattr(s, "use_real_llm", False)


def test_classify_categories():
    assert classify_proof_category(operation="list_inventory", intent="", request="show projects") == "inventory"
    assert classify_proof_category(operation="fetch_logs", intent="", request="logs") == "logs"
    assert classify_proof_category(operation="", intent="", request="continue") == "continue"
    assert is_continuity_prompt("what about api?")


def test_provider_confusion_detection():
    assert detect_provider_confusion(request="logs for killit", provider="railway", subject_label="railway / pilotos")
    assert not detect_provider_confusion(
        request="logs for aethos-api on railway", provider="railway", subject_label="railway / aethos-api"
    )


def test_capture_and_load_records():
    capture_kernel_reality_turn(
        request="show Railway projects",
        session_id="s1",
        source="chat",
        ok=True,
        intent="operational_kernel_list_inventory",
        meta={"readonly_provider": "railway", "goal_kind": "readonly_execute"},
        subject=SessionSubject(provider="railway", project="pilotos"),
    )
    rows = load_reality_records()
    assert len(rows) == 1
    assert rows[0]["provider"] == "railway"
    assert rows[0]["outcome"] == "success"


def test_live_metrics_incremented():
    capture_kernel_reality_turn(
        request="show logs",
        session_id="s2",
        source="cli",
        ok=True,
        intent="operational_kernel_fetch_logs",
        meta={"readonly_provider": "railway"},
        subject=SessionSubject(provider="railway"),
    )
    counters = snapshot_metrics().get("counters") or {}
    assert counters.get("kernel_turns", 0) >= 1
    assert counters.get("successful_turns", 0) >= 1


def test_kernel_router_captures_turn(enable_kernel):
    checks = {
        "ok": True,
        "railway_credential_ok": True,
        "railway_api_connection_ok": True,
        "inventory": {"ok": True, "project_count": 1, "projects": [{"name": "pilotos"}]},
    }
    with patch(
        "aethos_core.providers.railway.deployment_readiness.deployment_readiness_checks.safe_run_deployment_readiness_checks",
        return_value=checks,
    ):
        result = route_operational_conversation_kernel_turn("show Railway projects", session_id="cap-test")
    assert result is not None
    rows = load_reality_records()
    assert len(rows) == 1
    assert rows[0]["source"] == "chat"


def test_reality_summary_and_soak():
    for i in range(5):
        capture_kernel_reality_turn(
            request=f"show Railway projects {i}",
            session_id=f"s{i}",
            source="chat",
            ok=True,
            intent="operational_kernel_list_inventory",
            meta={"readonly_provider": "railway"},
            subject=SessionSubject(provider="railway"),
        )
    summary = compute_reality_summary(days=7)
    assert summary["total_turns"] == 5
    assert summary["provider_proof"]["railway"]["successful_turns"] == 5
    save_daily_snapshot(summary)
    soak = soak_progress(required_days=7)
    assert soak["days_recorded"] >= 1


def test_recovery_rate_ignores_unguided_failures():
    capture_kernel_reality_turn(
        request="show logs for invalid-project-xyz",
        session_id="r1",
        source="cli",
        ok=False,
        intent="operational_kernel_fetch_logs",
        meta={"readonly_provider": "vercel", "operation": "fetch_logs"},
        subject=SessionSubject(provider="vercel", vercel_project="invalid-project-xyz"),
    )
    capture_kernel_reality_turn(
        request="show logs for service-that-does-not-exist on railway",
        session_id="r2",
        source="cli",
        ok=False,
        intent="operational_kernel_fetch_logs",
        meta={"readonly_provider": "railway", "operation": "fetch_logs", "recovery_applied": "true"},
        subject=SessionSubject(provider="railway", service="service-that-does-not-exist"),
    )
    summary = compute_reality_summary(days=7)
    assert summary["recovery_success_rate"] == 1.0


def test_save_daily_refuses_empty_overwrite(tmp_path, monkeypatch):
    from aethos_core.operational_session import kernel_reality_registry as reg

    store = tmp_path / "operational_kernel_reality"
    store.mkdir()
    monkeypatch.setattr(reg, "_store_dir", lambda: store)

    prior = reg.save_daily_snapshot({"total_turns": 5, "successful_turns": 4})
    assert prior["summary"]["total_turns"] == 5
    kept = reg.save_daily_snapshot({"total_turns": 0, "successful_turns": 0})
    assert kept["summary"]["total_turns"] == 5
    assert kept["summary"].get("restore_warning")


def test_save_daily_synthetic_date_requires_dev_accelerate(tmp_path, monkeypatch):
    from aethos_core.operational_session import kernel_reality_registry as reg

    store = tmp_path / "operational_kernel_reality"
    store.mkdir()
    monkeypatch.setattr(reg, "_store_dir", lambda: store)
    monkeypatch.setenv("KERNEL_SOAK_DEV_ACCELERATE", "false")
    from aethos_core.config import get_settings

    get_settings.cache_clear()
    with pytest.raises(ValueError, match="KERNEL_SOAK_DEV_ACCELERATE"):
        reg.save_daily_snapshot({"total_turns": 3, "successful_turns": 3}, as_date="2026-06-10")

    monkeypatch.setenv("KERNEL_SOAK_DEV_ACCELERATE", "true")
    get_settings.cache_clear()
    saved = reg.save_daily_snapshot({"total_turns": 3, "successful_turns": 3}, as_date="2026-06-10")
    assert saved["date"] == "2026-06-10"


def test_restore_evidence_backup_roundtrip(tmp_path, monkeypatch):
    import shutil

    from aethos_core.operational_session import kernel_reality_registry as reg

    store = tmp_path / "operational_kernel_reality"
    store.mkdir()
    (store / "records.jsonl").write_text('{"record_id":"1","recovery_used":true,"outcome":"recovery"}\n', encoding="utf-8")
    evidence = tmp_path / "evidence" / "backup-2026-06-01"
    shutil.copytree(store, evidence)

    monkeypatch.setattr(reg, "_store_dir", lambda: store)
    monkeypatch.setattr(reg, "_evidence_root", lambda: tmp_path / "evidence")

    result = reg.restore_evidence_backup(day="2026-06-01")
    assert result["ok"] is True
    assert result["record_count"] == 1


def test_provider_routing_misroute_killit():
    routing = evaluate_provider_routing(request="logs for killit", resolved_provider="railway")
    assert routing.requested_provider == "vercel"
    assert routing.provider_misroute is True


def test_goal_completion_registry():
    record_readonly_goal_completed(
        session_id="g1",
        operation="fetch_logs",
        provider="vercel",
        user_text="logs for killit",
    )
    goals = goal_completion_summary()
    assert goals["goals_completed"] >= 1
    assert len(load_goal_records()) >= 1


def test_reality_summary_includes_extended_sections():
    capture_kernel_reality_turn(
        request="logs for killit",
        session_id="ext",
        source="chat",
        ok=True,
        intent="operational_kernel_fetch_logs",
        meta={"readonly_provider": "vercel"},
        subject=SessionSubject(provider="vercel", vercel_project="killit"),
    )
    summary = compute_reality_summary(days=7)
    assert "provider_routing" in summary
    assert "goal_completion" in summary
    assert "user_friction" in summary
    assert "success_report" in summary
    routing = provider_routing_summary(summary.get("total_turns") and load_reality_records() or [])
    assert routing is not None
    capture_kernel_reality_turn(
        request="give me top 5 logs for killit",
        session_id="v1",
        source="chat",
        ok=True,
        intent="operational_kernel_fetch_logs",
        meta={"readonly_provider": "vercel"},
        subject=SessionSubject(provider="vercel", vercel_project="killit"),
    )
    from aethos_core.cli.kernel_reality_report import cmd_kernel_reality_report

    assert cmd_kernel_reality_report(["--json"]) == 0

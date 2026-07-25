# SPDX-License-Identifier: Apache-2.0
"""Phase 9.6.5 GitHub workflow discovery recovery tests."""

from __future__ import annotations

from aethos_core.providers.github.shared.workflow_resolution import (
    _is_rerunnable_run,
    _select_rerunnable_candidate,
    resolve_latest_workflow_run,
)


def test_rerunnable_accepts_failed_and_cancelled_runs():
    failed = {"id": 1, "status": "completed", "conclusion": "failure", "run_number": 2}
    cancelled = {"id": 2, "status": "completed", "conclusion": "cancelled", "run_number": 3}
    active = {"id": 3, "status": "in_progress", "conclusion": None, "run_number": 4}
    assert _is_rerunnable_run(failed)[0] is True
    assert _is_rerunnable_run(cancelled)[0] is True
    assert _is_rerunnable_run(active)[0] is False


def test_select_rerunnable_prefers_latest_terminal_run():
    runs = [
        {"id": 1, "status": "in_progress", "conclusion": None, "run_number": 5, "created_at": "2026-01-03T00:00:00Z"},
        {"id": 2, "status": "completed", "conclusion": "failure", "run_number": 4, "created_at": "2026-01-02T00:00:00Z"},
        {"id": 3, "status": "completed", "conclusion": "success", "run_number": 3, "created_at": "2026-01-01T00:00:00Z"},
    ]
    selected, rejections = _select_rerunnable_candidate(runs)
    assert selected is not None
    assert selected["id"] == 2
    assert len(rejections) == 1


def test_discovery_failure_includes_diagnostics(monkeypatch):
    monkeypatch.setattr(
        "aethos_core.providers.github.shared.workflow_resolution.resolve_repository",
        lambda token, repository: {"ok": True, "full_name": "pilotmain/AethOS", "owner": "pilotmain", "repo": "AethOS"},
    )
    monkeypatch.setattr(
        "aethos_core.providers.github.shared.workflow_resolution.fetch_workflow_runs",
        lambda token, repository, limit=20: {
            "ok": True,
            "runs": [{"id": 9, "status": "in_progress", "conclusion": None, "workflow_id": 1, "run_number": 1}],
        },
    )
    out = resolve_latest_workflow_run("token", repository="AethOS")
    assert out["ok"] is False
    assert out["discovery_failure_reason"] == "no_rerunnable_candidate"
    debug = out.get("workflow_resolution_debug") or {}
    assert debug.get("workflow_candidates_found") == 1
    assert debug.get("rerunnable_candidates_found") == 0


def test_discovery_success_includes_debug(monkeypatch):
    monkeypatch.setattr(
        "aethos_core.providers.github.shared.workflow_resolution.resolve_repository",
        lambda token, repository: {"ok": True, "full_name": "pilotmain/AethOS", "owner": "pilotmain", "repo": "AethOS"},
    )
    monkeypatch.setattr(
        "aethos_core.providers.github.shared.workflow_resolution.fetch_workflow_runs",
        lambda token, repository, limit=20: {
            "ok": True,
            "runs": [
                {
                    "id": 42,
                    "status": "completed",
                    "conclusion": "failure",
                    "workflow_id": 99,
                    "name": "CI",
                    "run_number": 7,
                    "created_at": "2026-01-01T00:00:00Z",
                }
            ],
        },
    )
    out = resolve_latest_workflow_run("token", repository="AethOS")
    assert out["ok"] is True
    assert out["selected_run_id"] == 42
    assert out["workflow_resolution_debug"]["rerunnable_candidates_found"] == 1

# SPDX-License-Identifier: Apache-2.0
"""Phase 9.8E.5 — Tunnel bootstrap + engineering approval visibility."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

import pytest

from aethos_core.engineering.governance.engineering_preflight import run_and_record_engineering_preflight
from aethos_core.engineering.governance.engineering_preflight_store import (
    approve_preflight,
    clear_engineering_preflights_for_tests,
    deny_preflight,
    get_preflight,
    list_pending_preflights,
    record_engineering_preflight,
)
from aethos_core.engineering.governance.engineering_preflight import run_engineering_preflight
from aethos_core.runtime.jobs import job_store
from aethos_core.runtime.tunnel.tunnel_state import get_state, update_state


@pytest.fixture(autouse=True)
def _clean():
    clear_engineering_preflights_for_tests()
    yield
    clear_engineering_preflights_for_tests()


def test_preflight_creates_tracked_job(tmp_path: Path):
    repo = tmp_path / "repo"
    repo.mkdir()
    path = repo / "aethos_core/providers/github/shared/workflow_resolution.py"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("# x\n")
    preflight = run_and_record_engineering_preflight(
        user_request="Fix the GitHub workflow failure in AethOS",
        repo=repo,
        workspace_hint="aethos",
        source="test",
    )
    pending = list_pending_preflights()
    assert len(pending) == 1
    assert pending[0]["preflight_id"] == preflight["preflight_id"]
    assert pending[0]["approval_required"] is True
    assert pending[0]["approved"] is False
    job = job_store.get(pending[0]["job_id"])
    assert job is not None
    assert job.job_type == "engineering_preflight"
    assert job.params.get("approval_required") is True


def test_approve_e1_generates_pr_draft_only(tmp_path: Path):
    repo = tmp_path / "repo"
    repo.mkdir()
    preflight = run_engineering_preflight(user_request="fix workflow", repo=repo, persist=False)
    preflight["risk_tier"] = "E1_proposal_only"
    record_engineering_preflight(preflight=preflight, user_request="fix workflow", source="test")
    pid = preflight["preflight_id"]
    result = approve_preflight(pid)
    assert result.get("ok")
    row = get_preflight(pid)
    assert row.get("approved") is True
    assert result.get("execution", {}).get("proposal_only") is True
    assert result.get("execution", {}).get("pr_draft")


def test_deny_preflight(tmp_path: Path):
    repo = tmp_path / "repo"
    repo.mkdir()
    preflight = run_engineering_preflight(user_request="fix workflow", repo=repo, persist=False)
    record_engineering_preflight(preflight=preflight, user_request="fix workflow", source="test")
    pid = preflight["preflight_id"]
    result = deny_preflight(pid, reason="not now")
    assert result.get("ok")
    assert get_preflight(pid).get("denied") is True
    assert list_pending_preflights() == []


def test_tunnel_state_never_exposes_token():
    update_state(provider="ngrok", status="running", public_url="https://example.ngrok.io")
    state = get_state()
    assert "authtoken" not in str(state).lower()
    assert state.get("public_url") == "https://example.ngrok.io"


def test_tunnel_start_disabled_by_default():
    from aethos_core.runtime.tunnel.tunnel_manager import start_tunnel

    with patch("aethos_core.runtime.tunnel.tunnel_manager.get_settings") as mock_settings:
        mock_settings.return_value.telegram_tunnel_enabled = False
        result = start_tunnel()
    assert result.get("ok") is False

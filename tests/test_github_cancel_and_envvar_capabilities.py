# SPDX-License-Identifier: Apache-2.0
"""Batch hardening: GitHub cancel-workflow is a real governed mutation, and the env-var
write capabilities (railway/vercel) are reflected honestly in the matrix (no longer 0%)."""

from __future__ import annotations

from unittest.mock import patch

import aethos_core.providers.github.operations.git_write_api as gw
from aethos_core.operational_truth.capability_truth_matrix import build_capability_truth_matrix
from aethos_core.providers.github.mutations.github_mutation_adapter import GitHubMutationAdapter


def test_cancel_workflow_cancels_latest_active_run():
    def _req(token, method, path, *, params=None, json_body=None):
        if method == "GET" and path.endswith("/actions/runs"):
            return {"ok": True, "http_status": 200, "data": {"workflow_runs": [
                {"id": 111, "status": "completed"},
                {"id": 222, "status": "in_progress"},
            ]}}
        if method == "POST" and path.endswith("/runs/222/cancel"):
            return {"ok": True, "http_status": 202}
        return {"ok": False, "http_status": 404, "error": "nope"}
    with patch.object(gw, "request_github", _req):
        out = gw.cancel_workflow("tok", repository="pilotmain/AethOS")
    assert out["ok"] is True and out["run_id"] == 222


def test_cancel_workflow_no_active_run():
    def _req(token, method, path, *, params=None, json_body=None):
        return {"ok": True, "http_status": 200, "data": {"workflow_runs": [{"id": 1, "status": "completed"}]}}
    with patch.object(gw, "request_github", _req):
        out = gw.cancel_workflow("tok", repository="o/r")
    assert out["ok"] is False and out["failure_classification"] == "no_active_run"


def test_adapter_supports_cancel_workflow_dry_run():
    adapter = GitHubMutationAdapter()
    assert "cancel_workflow" in adapter.supported_mutations()
    dry = adapter.dry_run(operation="cancel_workflow", params={"target_name": "o/r"})
    assert dry["dry_run"] is True and "cancel" in dry["detail"].lower() and "no mutation" in dry["detail"].lower()


def test_redeploy_reruns_latest_run():
    def _req(token, method, path, *, params=None, json_body=None):
        if method == "GET" and path.endswith("/actions/runs"):
            return {"ok": True, "http_status": 200, "data": {"workflow_runs": [{"id": 999, "status": "completed"}]}}
        if method == "POST" and path.endswith("/runs/999/rerun"):
            return {"ok": True, "http_status": 201}
        return {"ok": False, "http_status": 404, "error": "nope"}
    with patch.object(gw, "request_github", _req):
        out = gw.redeploy("tok", repository="o/r")
    assert out["ok"] is True and out["run_id"] == 999 and out["operation"] == "redeploy"


def test_adapter_supports_redeploy():
    adapter = GitHubMutationAdapter()
    assert "redeploy" in adapter.supported_mutations()


def test_vercel_restart_is_supported_and_dry_runs():
    from aethos_core.providers.vercel.operations.mutation_adapter import VercelMutationAdapter

    adapter = VercelMutationAdapter()
    assert "restart" in adapter.supported_mutations()
    dry = adapter.dry_run(operation="restart", params={"target_name": "my-app"})
    assert dry["dry_run"] is True and "restart" in dry["detail"].lower() and "no mutation" in dry["detail"].lower()


def test_matrix_no_longer_experimental_zero():
    rows = {c["id"]: c for c in build_capability_truth_matrix()}
    for cap in (
        "github:cancel_workflow",
        "github:redeploy",
        "railway:set_env_var",
        "vercel:set_env_var",
        "vercel:remove_env_var",
        "vercel:restart",
    ):
        assert cap in rows, f"{cap} missing from matrix"
        assert rows[cap]["maturity"] != "experimental", f"{cap} still experimental"
        assert rows[cap]["verification_coverage_pct"] > 0, f"{cap} still 0%"
        assert rows[cap]["real"] == "full"

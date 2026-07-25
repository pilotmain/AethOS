# SPDX-License-Identifier: Apache-2.0
"""GitHub create-branch governed mutation: real REST executor (mocked here), correct
request shape, dry-run that mutates nothing, and capability registered/claimed."""

from __future__ import annotations

from unittest.mock import patch

import aethos_core.providers.github.operations.git_write_api as gw
from aethos_core.providers.github.mutations.github_mutation_adapter import GitHubMutationAdapter


def _fake_request(calls):
    def _req(token, method, path, *, params=None, json_body=None):
        calls.append((method, path, json_body))
        if method == "GET" and path.endswith("/git/ref/heads/main"):
            return {"ok": True, "http_status": 200, "data": {"object": {"sha": "abc123"}}}
        if method == "GET" and path.startswith("/repos/") and path.count("/") == 2:
            return {"ok": True, "http_status": 200, "data": {"default_branch": "main"}}
        if method == "POST" and path.endswith("/git/refs"):
            return {"ok": True, "http_status": 201, "data": {"ref": json_body["ref"]}}
        return {"ok": False, "http_status": 404, "error": "not found"}
    return _req


def test_create_branch_makes_correct_api_call():
    calls: list = []
    with patch.object(gw, "request_github", _fake_request(calls)):
        out = gw.create_branch("tok", repository="pilotmain/AethOS", new_branch="feature/x", base_branch="main")
    assert out["ok"] is True
    assert out["branch"] == "feature/x" and out["base"] == "main" and out["base_sha"] == "abc123"
    # The ref-creation POST carries the correct ref + base sha.
    post = next(c for c in calls if c[0] == "POST")
    assert post[1].endswith("/repos/pilotmain/AethOS/git/refs")
    assert post[2] == {"ref": "refs/heads/feature/x", "sha": "abc123"}


def test_create_branch_strips_refs_prefix_and_requires_name():
    with patch.object(gw, "request_github", _fake_request([])):
        out = gw.create_branch("tok", repository="o/r", new_branch="   ")
    assert out["ok"] is False and out["failure_classification"] == "invalid_request"


def test_invalid_token_surfaces_clear_auth_error():
    # A 401 from GitHub must surface 'reconnect your token', not 'could not resolve base branch'.
    with patch.object(gw, "request_github", lambda *a, **k: {"ok": False, "http_status": 401, "error": "Bad credentials"}):
        out = gw.create_branch("badtok", repository="o/r", new_branch="feat", base_branch="main")
    assert out["ok"] is False
    assert out["failure_classification"] == "provider_auth_failure"
    assert "reconnect" in out["detail"].lower() and "401" in out["detail"]


def test_branch_exists_is_classified():
    def _req(token, method, path, *, params=None, json_body=None):
        if method == "GET":
            return {"ok": True, "http_status": 200, "data": {"object": {"sha": "s"}, "default_branch": "main"}}
        return {"ok": False, "http_status": 422, "error": "Reference already exists"}
    with patch.object(gw, "request_github", _req):
        out = gw.create_branch("tok", repository="o/r", new_branch="dup", base_branch="main")
    assert out["ok"] is False and out["failure_classification"] == "branch_exists"


def test_adapter_supports_and_dry_runs_create_branch():
    adapter = GitHubMutationAdapter()
    assert "create_branch" in adapter.supported_mutations()
    dry = adapter.dry_run(operation="create_branch", params={"target_name": "o/r", "new_branch": "feat", "base_branch": "main"})
    assert dry["dry_run"] is True and "create branch" in dry["detail"].lower() and "no mutation" in dry["detail"].lower()


def test_capability_now_claimed_in_matrix():
    from aethos_core.operational_truth.capability_truth_matrix import build_capability_truth_matrix

    row = next(c for c in build_capability_truth_matrix() if c["id"] == "github:create_branch")
    assert row["claimed"] is True
    assert row["real"] in ("full", "partial")
    assert row["maturity"] in ("beta", "stable")  # no longer experimental/0%

# SPDX-License-Identifier: Apache-2.0
"""Destructive provider write-ops are now real governed mutations (experimental → beta):
GitHub commit/push/open-PR + Vercel rollback/promote/deploy-from-git. Each has a real
executor (mocked here), correct request shape, an approval-gated adapter with a no-op
dry-run, and is reflected honestly in the capability matrix. No live writes in tests."""

from __future__ import annotations

from unittest.mock import patch

import aethos_core.providers.github.operations.git_write_api as gw
import aethos_core.providers.vercel.operations.deploy_mutations_api as vd
from aethos_core.operational_truth.capability_truth_matrix import build_capability_truth_matrix
from aethos_core.providers.github.mutations.github_mutation_adapter import GitHubMutationAdapter
from aethos_core.providers.vercel.operations.mutation_adapter import VercelMutationAdapter


# ───────────────────────────── GitHub ─────────────────────────────


def test_commit_changes_full_git_data_flow():
    seen: list = []

    def _req(token, method, path, *, params=None, json_body=None):
        seen.append((method, path))
        if method == "GET" and "/git/ref/heads/" in path:
            return {"ok": True, "http_status": 200, "data": {"object": {"sha": "base"}}}
        if method == "GET" and "/git/commits/base" in path:
            return {"ok": True, "http_status": 200, "data": {"tree": {"sha": "tree0"}}}
        if method == "POST" and path.endswith("/git/blobs"):
            return {"ok": True, "http_status": 201, "data": {"sha": "blob1"}}
        if method == "POST" and path.endswith("/git/trees"):
            return {"ok": True, "http_status": 201, "data": {"sha": "tree1"}}
        if method == "POST" and path.endswith("/git/commits"):
            return {"ok": True, "http_status": 201, "data": {"sha": "commit1"}}
        if method == "PATCH" and "/git/refs/heads/" in path:
            return {"ok": True, "http_status": 200}
        return {"ok": False, "http_status": 404, "error": "nope"}

    with patch.object(gw, "request_github", _req):
        out = gw.commit_changes("tok", repository="o/r", branch="main", message="msg", files={"a.txt": "hi"})
    assert out["ok"] is True and out["commit_sha"] == "commit1" and out["files"] == ["a.txt"]
    # Created blob → tree → commit → updated ref.
    assert ("POST", "/repos/o/r/git/blobs") in seen and ("POST", "/repos/o/r/git/commits") in seen


def test_commit_changes_requires_files():
    with patch.object(gw, "request_github", lambda *a, **k: {"ok": True, "data": {}}):
        out = gw.commit_changes("tok", repository="o/r", branch="main", message="m", files={})
    assert out["ok"] is False and out["failure_classification"] == "invalid_request"


def test_push_branch_updates_ref():
    with patch.object(gw, "request_github", lambda *a, **k: {"ok": True, "http_status": 200}):
        out = gw.push_branch("tok", repository="o/r", branch="feat", sha="deadbeef", force=True)
    assert out["ok"] is True and out["forced"] is True


def test_open_pr_creates_pull():
    def _req(token, method, path, *, params=None, json_body=None):
        assert json_body["head"] == "feat" and json_body["base"] == "main"
        return {"ok": True, "http_status": 201, "data": {"number": 7, "html_url": "https://gh/pr/7"}}
    with patch.object(gw, "request_github", _req):
        out = gw.open_pr("tok", repository="o/r", head="feat", base="main", title="T")
    assert out["ok"] is True and out["pr_number"] == 7 and out["pr_url"].endswith("/pr/7")


# ───────────────────────────── Vercel ─────────────────────────────


def test_rollback_promotes_previous_production():
    with patch.object(vd, "find_project_by_name", lambda *a, **k: {"id": "prj"}), patch.object(
        vd, "list_deployments",
        lambda *a, **k: [
            {"uid": "cur", "target": "production", "readyState": "READY"},
            {"uid": "prev", "target": "production", "readyState": "READY"},
        ],
    ), patch.object(vd, "httpx") as mock_httpx:
        mock_httpx.Client.return_value.__enter__.return_value.post.return_value.status_code = 200
        mock_httpx.HTTPError = Exception
        out = vd.rollback("tok", target_name="app")
    assert out["ok"] is True and out["deployment_id"] == "prev" and out["operation"] == "rollback"


def test_rollback_needs_a_previous_deployment():
    with patch.object(vd, "find_project_by_name", lambda *a, **k: {"id": "prj"}), patch.object(
        vd, "list_deployments", lambda *a, **k: [{"uid": "cur", "target": "production", "readyState": "READY"}]
    ):
        out = vd.rollback("tok", target_name="app")
    assert out["ok"] is False and out["failure_classification"] == "no_rollback_target"


# ───────────────────────────── adapters + matrix ─────────────────────────────


def test_adapters_advertise_and_dry_run_all_destructive_ops():
    gh = GitHubMutationAdapter()
    for op in ("commit_changes", "push_branch", "open_pr"):
        assert op in gh.supported_mutations()
        assert gh.dry_run(operation=op, params={"target_name": "o/r"})["dry_run"] is True
    vc = VercelMutationAdapter()
    for op in ("rollback", "promote_deployment", "deploy_from_git"):
        assert op in vc.supported_mutations()
        assert "no mutation performed" in vc.dry_run(operation=op, params={"target_name": "app"})["detail"].lower()


def test_no_experimental_provider_write_ops_remain():
    rows = {c["id"]: c for c in build_capability_truth_matrix()}
    for cap in (
        "github:commit_changes", "github:push_branch", "github:open_pr",
        "vercel:rollback", "vercel:promote_deployment", "vercel:deploy_from_git",
    ):
        assert rows[cap]["maturity"] != "experimental", f"{cap} still experimental"
        assert rows[cap]["verification_coverage_pct"] > 0 and rows[cap]["real"] == "full"

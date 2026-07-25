# SPDX-License-Identifier: Apache-2.0
"""GitHub governed git-write mutations — branch/commit/push/PR (real REST API).

Each function performs the real GitHub API call and returns a normalized
{ok, detail/evidence, http_status, failure_classification} shape. Governance
(approval) is enforced by the mutation adapter/execution layer above — these
are the substrate, not the gate.
"""

from __future__ import annotations

from typing import Any

from aethos_core.providers.github.api_client import parse_owner_repo, request_github


def _auth_failure(res: dict[str, Any]) -> dict[str, Any] | None:
    """If a GitHub response is an auth failure (401/403), return a clear, actionable error
    so callers surface 'reconnect your token' instead of a confusing downstream message."""
    status = res.get("http_status")
    if status in (401, 403):
        return {
            "ok": False,
            "detail": (
                f"GitHub credential is invalid or lacks write scope (HTTP {status}). "
                "Reconnect a GitHub token with repo write access in Mission Control → "
                "Advanced settings → Credentials."
            ),
            "failure_classification": "provider_auth_failure",
            "http_status": status,
        }
    return None


def _default_branch(token: str, owner: str, repo: str) -> str | None:
    res = request_github(token, "GET", f"/repos/{owner}/{repo}")
    if res.get("ok"):
        return str((res.get("data") or {}).get("default_branch") or "") or None
    return None


def _branch_sha(token: str, owner: str, repo: str, branch: str) -> tuple[str | None, dict[str, Any]]:
    res = request_github(token, "GET", f"/repos/{owner}/{repo}/git/ref/heads/{branch}")
    data = res.get("data") if isinstance(res.get("data"), dict) else {}
    sha = (data.get("object") or {}).get("sha") if isinstance(data.get("object"), dict) else None
    return (str(sha) if sha else None), res


def create_branch(
    token: str, *, repository: str, new_branch: str, base_branch: str | None = None
) -> dict[str, Any]:
    """Create a new branch (git ref) from a base branch. Reversible (delete the ref)."""
    owner, repo = parse_owner_repo(repository)
    if not owner or not repo:
        return {"ok": False, "detail": "Could not parse owner/repo.", "failure_classification": "target_unresolved"}
    name = (new_branch or "").strip()
    if name.startswith("refs/heads/"):
        name = name[len("refs/heads/") :]
    if not name:
        return {"ok": False, "detail": "New branch name required.", "failure_classification": "invalid_request"}
    base = (base_branch or "").strip() or _default_branch(token, owner, repo) or "main"
    sha, base_res = _branch_sha(token, owner, repo, base)
    if not sha:
        auth = _auth_failure(base_res)
        if auth:
            return auth
        return {
            "ok": False,
            "detail": f"Could not resolve base branch '{base}'.",
            "failure_classification": "base_unresolved",
            "http_status": base_res.get("http_status"),
        }
    res = request_github(
        token,
        "POST",
        f"/repos/{owner}/{repo}/git/refs",
        json_body={"ref": f"refs/heads/{name}", "sha": sha},
    )
    status = res.get("http_status")
    if res.get("ok") or status in (200, 201):
        return {
            "ok": True,
            "provider": "github",
            "operation": "create_branch",
            "repository": repository,
            "branch": name,
            "base": base,
            "base_sha": sha,
            "http_status": status or 201,
            "detail": f"Created branch `{name}` from `{base}` in `{repository}`.",
        }
    err = str(res.get("error") or "create branch failed")[:240]
    classification = "branch_exists" if status == 422 else "provider_error"
    return {"ok": False, "detail": err, "failure_classification": classification, "http_status": status}


def cancel_workflow(token: str, *, repository: str, run_id: str | int | None = None) -> dict[str, Any]:
    """Cancel a GitHub Actions run. If no run_id, cancels the latest in-flight run."""
    owner, repo = parse_owner_repo(repository)
    if not owner or not repo:
        return {"ok": False, "detail": "Could not parse owner/repo.", "failure_classification": "target_unresolved"}

    target_run = run_id
    if not target_run:
        listing = request_github(
            token, "GET", f"/repos/{owner}/{repo}/actions/runs", params={"per_page": 30}
        )
        if not listing.get("ok"):
            auth = _auth_failure(listing)
            if auth:
                return auth
            return {
                "ok": False,
                "detail": str(listing.get("error") or "Could not list workflow runs.")[:240],
                "failure_classification": "provider_error",
                "http_status": listing.get("http_status"),
            }
        runs = (listing.get("data") or {}).get("workflow_runs") or []
        active = {"in_progress", "queued", "requested", "waiting", "pending"}
        live = [r for r in runs if str(r.get("status")) in active]
        if not live:
            return {"ok": False, "detail": "No in-flight workflow run to cancel.", "failure_classification": "no_active_run"}
        target_run = live[0].get("id")

    res = request_github(token, "POST", f"/repos/{owner}/{repo}/actions/runs/{target_run}/cancel")
    status = res.get("http_status")
    if res.get("ok") or status in (202, 200):
        return {
            "ok": True,
            "provider": "github",
            "operation": "cancel_workflow",
            "repository": repository,
            "run_id": target_run,
            "http_status": status or 202,
            "detail": f"Requested cancel of workflow run `{target_run}` in `{repository}`.",
        }
    err = str(res.get("error") or "cancel failed")[:240]
    classification = "already_complete" if status == 409 else "provider_error"
    return {"ok": False, "detail": err, "failure_classification": classification, "http_status": status}


def redeploy(token: str, *, repository: str) -> dict[str, Any]:
    """Re-deploy by re-running the most recent workflow run (the deploy pipeline)."""
    owner, repo = parse_owner_repo(repository)
    if not owner or not repo:
        return {"ok": False, "detail": "Could not parse owner/repo.", "failure_classification": "target_unresolved"}
    listing = request_github(token, "GET", f"/repos/{owner}/{repo}/actions/runs", params={"per_page": 1})
    if not listing.get("ok"):
        auth = _auth_failure(listing)
        if auth:
            return auth
        return {
            "ok": False,
            "detail": str(listing.get("error") or "Could not list workflow runs.")[:240],
            "failure_classification": "provider_error",
            "http_status": listing.get("http_status"),
        }
    runs = (listing.get("data") or {}).get("workflow_runs") or []
    if not runs:
        return {"ok": False, "detail": "No workflow run to redeploy.", "failure_classification": "no_run"}
    run_id = runs[0].get("id")
    res = request_github(token, "POST", f"/repos/{owner}/{repo}/actions/runs/{run_id}/rerun")
    status = res.get("http_status")
    if res.get("ok") or status in (201, 202):
        return {
            "ok": True,
            "provider": "github",
            "operation": "redeploy",
            "repository": repository,
            "run_id": run_id,
            "http_status": status or 201,
            "detail": f"Re-running latest workflow run `{run_id}` in `{repository}` (redeploy).",
        }
    return {"ok": False, "detail": str(res.get("error") or "redeploy failed")[:240], "failure_classification": "provider_error", "http_status": status}


def commit_changes(
    token: str, *, repository: str, branch: str, message: str, files: dict[str, str]
) -> dict[str, Any]:
    """Commit a set of {path: content} files to a branch via the Git Data API."""
    owner, repo = parse_owner_repo(repository)
    if not owner or not repo:
        return {"ok": False, "detail": "Could not parse owner/repo.", "failure_classification": "target_unresolved"}
    if not branch:
        return {"ok": False, "detail": "Branch required.", "failure_classification": "invalid_request"}
    if not message:
        return {"ok": False, "detail": "Commit message required.", "failure_classification": "invalid_request"}
    if not files:
        return {"ok": False, "detail": "No file changes provided.", "failure_classification": "invalid_request"}

    base_sha, ref_res = _branch_sha(token, owner, repo, branch)
    if not base_sha:
        auth = _auth_failure(ref_res)
        if auth:
            return auth
        return {"ok": False, "detail": f"Could not resolve branch '{branch}'.", "failure_classification": "base_unresolved", "http_status": ref_res.get("http_status")}
    commit_res = request_github(token, "GET", f"/repos/{owner}/{repo}/git/commits/{base_sha}")
    base_tree = ((commit_res.get("data") or {}).get("tree") or {}).get("sha") if commit_res.get("ok") else None
    if not base_tree:
        return {"ok": False, "detail": "Could not resolve base tree.", "failure_classification": "provider_error"}

    tree_items = []
    for path, content in files.items():
        blob = request_github(token, "POST", f"/repos/{owner}/{repo}/git/blobs", json_body={"content": content, "encoding": "utf-8"})
        blob_sha = (blob.get("data") or {}).get("sha") if blob.get("ok") else None
        if not blob_sha:
            return {"ok": False, "detail": f"Failed to create blob for `{path}`.", "failure_classification": "provider_error"}
        tree_items.append({"path": path, "mode": "100644", "type": "blob", "sha": blob_sha})

    tree = request_github(token, "POST", f"/repos/{owner}/{repo}/git/trees", json_body={"base_tree": base_tree, "tree": tree_items})
    tree_sha = (tree.get("data") or {}).get("sha") if tree.get("ok") else None
    if not tree_sha:
        return {"ok": False, "detail": "Failed to create tree.", "failure_classification": "provider_error"}

    commit = request_github(token, "POST", f"/repos/{owner}/{repo}/git/commits", json_body={"message": message, "tree": tree_sha, "parents": [base_sha]})
    new_sha = (commit.get("data") or {}).get("sha") if commit.get("ok") else None
    if not new_sha:
        return {"ok": False, "detail": "Failed to create commit.", "failure_classification": "provider_error"}

    upd = request_github(token, "PATCH", f"/repos/{owner}/{repo}/git/refs/heads/{branch}", json_body={"sha": new_sha})
    if upd.get("ok") or upd.get("http_status") in (200, 201):
        return {
            "ok": True, "provider": "github", "operation": "commit_changes", "repository": repository,
            "branch": branch, "commit_sha": new_sha, "files": list(files.keys()),
            "detail": f"Committed {len(files)} file(s) to `{branch}` in `{repository}` ({new_sha[:7]}).",
        }
    return {"ok": False, "detail": str(upd.get("error") or "Failed to update branch ref.")[:240], "failure_classification": "provider_error", "http_status": upd.get("http_status")}


def push_branch(token: str, *, repository: str, branch: str, sha: str, force: bool = False) -> dict[str, Any]:
    """Update (push) a branch ref to a target commit sha. API equivalent of `git push`."""
    owner, repo = parse_owner_repo(repository)
    if not owner or not repo:
        return {"ok": False, "detail": "Could not parse owner/repo.", "failure_classification": "target_unresolved"}
    if not branch or not sha:
        return {"ok": False, "detail": "Branch and target sha required.", "failure_classification": "invalid_request"}
    res = request_github(token, "PATCH", f"/repos/{owner}/{repo}/git/refs/heads/{branch}", json_body={"sha": sha, "force": bool(force)})
    status = res.get("http_status")
    if res.get("ok") or status in (200, 201):
        return {"ok": True, "provider": "github", "operation": "push_branch", "repository": repository, "branch": branch, "sha": sha, "forced": bool(force), "http_status": status or 200, "detail": f"Updated `{branch}` to `{sha[:7]}`{' (forced)' if force else ''} in `{repository}`."}
    classification = "non_fast_forward" if status == 422 else "provider_error"
    return {"ok": False, "detail": str(res.get("error") or "push failed")[:240], "failure_classification": classification, "http_status": status}


def open_pr(token: str, *, repository: str, head: str, base: str, title: str, body: str = "") -> dict[str, Any]:
    """Open a pull request from `head` into `base`."""
    owner, repo = parse_owner_repo(repository)
    if not owner or not repo:
        return {"ok": False, "detail": "Could not parse owner/repo.", "failure_classification": "target_unresolved"}
    if not head or not base or not title:
        return {"ok": False, "detail": "head, base, and title are required.", "failure_classification": "invalid_request"}
    res = request_github(token, "POST", f"/repos/{owner}/{repo}/pulls", json_body={"title": title, "head": head, "base": base, "body": body})
    status = res.get("http_status")
    if res.get("ok") or status in (200, 201):
        data = res.get("data") or {}
        return {"ok": True, "provider": "github", "operation": "open_pr", "repository": repository, "pr_number": data.get("number"), "pr_url": data.get("html_url"), "http_status": status or 201, "detail": f"Opened PR #{data.get('number')} ({head} → {base}) in `{repository}`."}
    classification = "pr_exists" if status == 422 else "provider_error"
    return {"ok": False, "detail": str(res.get("error") or "open PR failed")[:240], "failure_classification": classification, "http_status": status}

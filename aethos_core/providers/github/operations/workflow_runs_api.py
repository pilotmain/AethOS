# SPDX-License-Identifier: Apache-2.0
"""GitHub Actions workflow runs API."""

from __future__ import annotations

from typing import Any

from aethos_core.providers.github.api_client import parse_owner_repo, request_github


def fetch_workflow_runs(token: str, *, repository: str, limit: int = 20) -> dict[str, Any]:
    owner, repo = parse_owner_repo(repository)
    if not owner or not repo:
        return {
            "ok": False,
            "source": "provider_api",
            "error": f"Repository `{repository}` is not a valid owner/repo target.",
            "runs": [],
        }
    result = request_github(
        token,
        "GET",
        f"/repos/{owner}/{repo}/actions/runs",
        params={"per_page": min(limit, 100)},
    )
    if not result.get("ok"):
        return {
            "ok": False,
            "source": "provider_api",
            "error": str(result.get("error") or "GitHub Actions API request failed."),
            "runs": [],
            "repository": f"{owner}/{repo}",
        }
    data = result.get("data") if isinstance(result.get("data"), dict) else {}
    runs: list[dict[str, Any]] = []
    for row in data.get("workflow_runs") or []:
        if not isinstance(row, dict):
            continue
        runs.append(
            {
                "id": row.get("id"),
                "workflow_id": row.get("workflow_id"),
                "name": row.get("name"),
                "status": row.get("status"),
                "conclusion": row.get("conclusion"),
                "event": row.get("event"),
                "head_branch": row.get("head_branch"),
                "head_sha": row.get("head_sha"),
                "html_url": row.get("html_url"),
                "created_at": row.get("created_at"),
                "updated_at": row.get("updated_at"),
                "run_number": row.get("run_number"),
                "actor": (
                    (row.get("actor") or {}).get("login")
                    if isinstance(row.get("actor"), dict)
                    else None
                ),
            }
        )
    return {
        "ok": True,
        "source": "provider_api",
        "repository": f"{owner}/{repo}",
        "run_count": len(runs),
        "runs": runs[:limit],
    }


def fetch_workflow_runs_for_workflow(
    token: str,
    *,
    repository: str,
    workflow_id: str | int,
    limit: int = 20,
) -> dict[str, Any]:
    owner, repo = parse_owner_repo(repository)
    if not owner or not repo:
        return {
            "ok": False,
            "source": "provider_api",
            "error": f"Repository `{repository}` is not a valid owner/repo target.",
            "runs": [],
        }
    result = request_github(
        token,
        "GET",
        f"/repos/{owner}/{repo}/actions/workflows/{workflow_id}/runs",
        params={"per_page": min(limit, 100)},
    )
    if not result.get("ok"):
        return {
            "ok": False,
            "source": "provider_api",
            "error": str(result.get("error") or "GitHub workflow runs API request failed."),
            "runs": [],
            "repository": f"{owner}/{repo}",
        }
    data = result.get("data") if isinstance(result.get("data"), dict) else {}
    runs: list[dict[str, Any]] = []
    for row in data.get("workflow_runs") or []:
        if not isinstance(row, dict):
            continue
        runs.append(
            {
                "id": row.get("id"),
                "workflow_id": row.get("workflow_id"),
                "name": row.get("name"),
                "status": row.get("status"),
                "conclusion": row.get("conclusion"),
                "event": row.get("event"),
                "head_branch": row.get("head_branch"),
                "head_sha": row.get("head_sha"),
                "html_url": row.get("html_url"),
                "created_at": row.get("created_at"),
                "updated_at": row.get("updated_at"),
                "run_number": row.get("run_number"),
                "actor": (
                    (row.get("actor") or {}).get("login")
                    if isinstance(row.get("actor"), dict)
                    else None
                ),
            }
        )
    return {
        "ok": True,
        "source": "provider_api",
        "repository": f"{owner}/{repo}",
        "workflow_id": workflow_id,
        "run_count": len(runs),
        "runs": runs[:limit],
    }


def format_workflow_runs_output(payload: dict[str, Any]) -> str:
    if not payload.get("ok"):
        return str(payload.get("error") or "Workflow run fetch failed.")
    lines = [
        f"Repository: {payload.get('repository')}",
        f"Workflow runs ({payload.get('run_count', 0)}):",
        "",
    ]
    for run in payload.get("runs") or []:
        status = run.get("status") or "unknown"
        conclusion = run.get("conclusion") or "—"
        lines.append(
            f"- **{run.get('name') or 'workflow'}** · run #{run.get('run_number')} · "
            f"status `{status}` · conclusion `{conclusion}` · branch `{run.get('head_branch') or '—'}`"
        )
        if run.get("head_sha"):
            lines.append(f"  - commit `{str(run['head_sha'])[:12]}`")
    if len(lines) <= 3:
        lines.append("(no workflow runs returned)")
    return "\n".join(lines)

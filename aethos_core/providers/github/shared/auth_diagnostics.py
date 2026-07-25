# SPDX-License-Identifier: Apache-2.0
"""GitHub auth diagnostics for workflow discovery — separates auth vs discovery failures."""

from __future__ import annotations

from typing import Any

from aethos_core.connections.validation_status import INVALID, MISSING, VALIDATED
from aethos_core.providers.github.api_client import list_repositories, test_connection
from aethos_core.providers.github.operations.workflow_runs_api import fetch_workflow_runs
from aethos_core.providers.github.shared.workflow_resolution import resolve_repository
from aethos_core.security.secret_redaction import redact_text


def github_discovery_auth_diagnostics(token: str | None, *, repository: str) -> dict[str, Any]:
    if not token:
        return {
            "auth_state": MISSING,
            "workflow_scope_present": False,
            "repository_access": False,
            "api_status": None,
            "repository": repository,
            "workflow_runs_visible": 0,
            "detail": "No GitHub token available.",
        }

    conn = test_connection(token)
    auth_ok = bool(conn.get("ok"))
    auth_state = VALIDATED if auth_ok else INVALID
    api_status = 200 if auth_ok else 401

    repo_access = False
    workflow_scope = False
    runs_visible = 0
    resolved_repo = repository

    if auth_ok:
        listed = list_repositories(token)
        repo_access = bool(listed.get("ok"))
        if not repo_access:
            auth_state = "insufficient_scope"

        repo_result = resolve_repository(token, repository=repository)
        if repo_result.get("ok"):
            resolved_repo = str(repo_result.get("full_name") or repository)
            runs_payload = fetch_workflow_runs(token, repository=resolved_repo, limit=20)
            if runs_payload.get("ok"):
                runs = runs_payload.get("runs") or []
                runs_visible = len(runs)
                workflow_scope = runs_visible > 0
            else:
                detail = redact_text(str(runs_payload.get("error") or ""))
                if "403" in detail or "404" in detail:
                    auth_state = "insufficient_scope"

    return {
        "auth_state": auth_state,
        "workflow_scope_present": workflow_scope,
        "repository_access": repo_access,
        "api_status": api_status,
        "repository": resolved_repo,
        "workflow_runs_visible": runs_visible,
        "account_login": conn.get("account_login") if auth_ok else None,
        "detail": None if auth_ok else redact_text(str(conn.get("detail") or "auth failed")),
    }

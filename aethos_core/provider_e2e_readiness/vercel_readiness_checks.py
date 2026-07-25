# SPDX-License-Identifier: Apache-2.0
"""Readonly Vercel deployment readiness checks."""

from __future__ import annotations

from typing import Any

from aethos_core.config import get_settings


def run_vercel_readiness_checks(*, session_id: str = "default") -> dict[str, Any]:
    _ = session_id
    settings = get_settings()
    checks: dict[str, Any] = {
        "vercel_credential_ok": False,
        "vercel_credential_detail": "",
        "vercel_api_connection_ok": False,
        "vercel_api_connection_detail": "",
        "vercel_project_count": 0,
        "vercel_projects": [],
        "mutation_execution_enabled": settings.mutation_execution_enabled,
        "provider_env_var_mutations_enabled": settings.provider_env_var_mutations_enabled,
    }

    from aethos_core.providers.vercel.auth import VercelAuthAdapter

    auth = VercelAuthAdapter()
    resolved = auth.resolve_best_auth_method(operation="read_projects")
    if resolved.get("method") != "api_token":
        checks["vercel_credential_detail"] = str(resolved.get("detail") or "Vercel API token not configured.")
        return checks

    credential_id = str(resolved.get("credential_id") or "")
    token = auth.get_api_token(credential_id)
    if not token:
        checks["vercel_credential_detail"] = "Vercel token could not be loaded from the credential vault."
        return checks

    checks["vercel_credential_ok"] = True
    try:
        from aethos_core.providers.vercel.api_client import list_projects, test_connection

        conn = test_connection(token)
        checks["vercel_api_connection_ok"] = bool(conn.get("ok"))
        checks["vercel_api_connection_detail"] = str(conn.get("detail") or "")
        projects = list_projects(token)
        checks["vercel_project_count"] = len(projects)
        checks["vercel_projects"] = [
            {"name": str(p.get("name") or ""), "id": str(p.get("id") or "")} for p in projects[:12]
        ]
    except Exception as exc:
        checks["vercel_api_connection_ok"] = False
        checks["vercel_api_connection_detail"] = str(exc)

    return checks

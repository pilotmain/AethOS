# SPDX-License-Identifier: Apache-2.0
"""Generic provider agent operations — domain verbs with provider param."""

from __future__ import annotations

import json
from typing import Any

from aethos_core.execution_brain.cloud_provider_catalog import (
    FIRST_CLASS_AGENT_PROVIDERS,
    list_agent_cloud_providers,
    normalize_provider_name,
    provider_display_name,
)
from aethos_core.execution_brain.cloud_agent_bridge import (
    discover_provider_inventory,
    resolve_provider_token,
    validate_provider_connection,
)
from aethos_core.execution_brain.provider_connection_cache import cache_get, cache_set

_WORKFLOW_PROVIDERS = frozenset({"github"})

# Short-TTL caches for repeated readonly questions in a session (§C4). A successful
# mutation invalidates the provider's reads (see operations/mutations/execution.py).
_INVENTORY_TTL_SEC = 30.0
_HEALTH_TTL_SEC = 20.0
_LOGS_TTL_SEC = 15.0


def provider_catalog_payload() -> dict[str, Any]:
    from aethos_core.execution_brain.agent_tool_catalog import list_model_facing_tool_names
    from aethos_core.execution_brain.provider_inventory_registry import (
        CUSTOM_INVENTORY_FETCHERS,
        HTTP_INVENTORY_SPECS,
    )

    rows = []
    for name in list_agent_cloud_providers():
        caps = []
        if name in FIRST_CLASS_AGENT_PROVIDERS:
            caps.extend(["validate", "inventory", "health", "logs"])
        elif name in _WORKFLOW_PROVIDERS:
            caps.extend(["validate", "inventory", "workflows", "health"])
        elif name in HTTP_INVENTORY_SPECS or name in CUSTOM_INVENTORY_FETCHERS:
            caps.extend(["validate", "inventory", "health"])
        else:
            caps.append("validate")
        rows.append(
            {
                "provider": name,
                "label": provider_display_name(name),
                "capabilities": caps,
            }
        )
    return {
        "ok": True,
        "provider_count": len(rows),
        "providers": rows,
        "agent_tools": list_model_facing_tool_names(),
        "credential_source": "mission_control_vault",
    }


def provider_validate(provider: str) -> dict[str, Any]:
    return validate_provider_connection(provider)


def provider_inventory(provider: str, *, session_id: str = "default") -> dict[str, Any]:
    cache_key = normalize_provider_name(provider) or (provider or "")
    cached = cache_get(cache_key, op="inventory")
    if cached is not None:
        return cached
    result = discover_provider_inventory(provider, session_id=session_id)
    if isinstance(result, dict) and result.get("ok"):
        cache_set(cache_key, result, op="inventory", ttl_sec=_INVENTORY_TTL_SEC)
    return result


def provider_inventory_all(
    *,
    session_id: str = "default",
    limit: int = 40,
    mode: str = "quick",
) -> dict[str, Any]:
    """Scan providers. mode=quick validates only (fast); mode=full includes inventory."""
    mode_key = (mode or "quick").strip().lower()
    names = list_agent_cloud_providers()[: max(1, min(limit, 50))]

    def _row_for(name: str) -> dict[str, Any]:
        validation = validate_provider_connection(name)
        row: dict[str, Any] = {
            "provider": name,
            "label": provider_display_name(name),
            "connection_ok": bool(validation.get("ok")),
            "detail": validation.get("detail") or validation.get("error"),
        }
        if validation.get("ok") and mode_key == "full":
            inv = discover_provider_inventory(name, session_id=session_id)
            row["inventory_ok"] = bool(inv.get("ok"))
            row["inventory"] = inv.get("inventory")
            row["inventory_error"] = inv.get("error")
        return row

    if mode_key == "quick" and len(names) > 1:
        from concurrent.futures import ThreadPoolExecutor

        from aethos_core.tenancy import get_current_tenant, tenant_scope

        scoped_tenant = get_current_tenant()

        def _row_for_scoped(name: str) -> dict[str, Any]:
            with tenant_scope(scoped_tenant):
                return _row_for(name)

        with ThreadPoolExecutor(max_workers=min(8, len(names))) as pool:
            rows = list(pool.map(_row_for_scoped, names))
    else:
        rows = [_row_for(name) for name in names]

    configured = sum(1 for row in rows if row.get("connection_ok"))
    return {
        "ok": configured > 0,
        "mode": mode_key,
        "provider_count": len(rows),
        "configured_count": configured,
        "providers": rows,
        "session_id": session_id,
        "credential_source": "mission_control_vault",
    }


def provider_health(
    provider: str,
    *,
    target_name: str = "",
    project_name: str = "",
    limit: int = 3,
    session_id: str = "default",
) -> dict[str, Any]:
    canonical = normalize_provider_name(provider)
    if not canonical:
        return {"ok": False, "error": "unknown_provider", "provider": provider}

    target = str(target_name or project_name or "").strip()
    lim = max(1, min(int(limit or 3), 10))

    cached = cache_get(canonical, op="health", target=target)
    if cached is not None:
        return cached

    def _compute() -> dict[str, Any]:
        if canonical == "vercel":
            from aethos_core.execution_brain.agent_tool_executor import _execute_vercel_deployment_health

            payload = json.loads(
                _execute_vercel_deployment_health({"project_name": target, "limit": lim})
            )
            return {"ok": bool(payload.get("ok", True)), "provider": canonical, "health": payload}

        if canonical == "railway":
            from aethos_core.execution_brain.agent_tool_executor import (
                _execute_railway_inventory_health,
                _execute_railway_service_health,
            )

            if target:
                payload = json.loads(_execute_railway_service_health({"service_name": target, "project_name": project_name}))
            else:
                payload = json.loads(_execute_railway_inventory_health({"service_name": target}))
            return {"ok": bool(payload.get("ok")), "provider": canonical, "health": payload}

        if canonical == "github" and target:
            wf = provider_workflows(canonical, repository=target, limit=lim, session_id=session_id)
            runs = list((wf.get("workflows") or {}).get("runs") or [])
            return {
                "ok": bool(wf.get("ok")),
                "provider": canonical,
                "health": {
                    "repository": target,
                    "recent_runs": runs[:lim],
                    "failed_count": sum(1 for r in runs if str(r.get("conclusion") or "") == "failure"),
                },
                "error": wf.get("error"),
            }

        inv = discover_provider_inventory(canonical, session_id=session_id)
        resources = list((inv.get("inventory") or {}).get("resources") or [])
        if target:
            needle = target.lower()
            resources = [
                r
                for r in resources
                if needle in str(r.get("name") or "").lower() or str(r.get("name") or "").lower() in needle
            ]
        health_rows = [
            {"name": r.get("name"), "status": r.get("status") or "unknown", "provider": canonical}
            for r in resources[:25]
            if isinstance(r, dict)
        ]
        return {
            "ok": bool(health_rows) or bool(inv.get("ok")),
            "provider": canonical,
            "health": {"rows": health_rows, "resource_count": len(health_rows)},
            "error": inv.get("error") if not health_rows else None,
        }

    result = _compute()
    if isinstance(result, dict) and result.get("ok"):
        cache_set(canonical, result, op="health", target=target, ttl_sec=_HEALTH_TTL_SEC)
    return result


def provider_logs(
    provider: str,
    *,
    target_name: str,
    limit: int = 20,
    session_id: str = "default",
) -> dict[str, Any]:
    _ = session_id
    canonical = normalize_provider_name(provider)
    if not canonical:
        return {"ok": False, "error": "unknown_provider"}
    target = str(target_name or "").strip()
    if not target:
        return {"ok": False, "error": "target_name_required"}

    cached = cache_get(canonical, op="logs", target=f"{target}:{limit}")
    if cached is not None:
        return cached

    def _compute() -> dict[str, Any]:
        if canonical == "vercel":
            from aethos_core.execution_brain.agent_tool_executor import _execute_vercel_fetch_logs

            return json.loads(_execute_vercel_fetch_logs({"project_name": target, "limit": limit}))

        if canonical == "railway":
            from aethos_core.execution_brain.agent_tool_executor import _execute_railway_fetch_logs

            return json.loads(_execute_railway_fetch_logs({"service_name": target, "limit": limit}))

        if canonical == "github":
            token, err = resolve_provider_token("github")
            if not token:
                return {"ok": False, "provider": canonical, "error": err or "token_not_configured"}
            from aethos_core.providers.github.operations.workflow_jobs_api import fetch_workflow_jobs

            payload = fetch_workflow_jobs(token, repository=target, run_limit=max(1, min(limit, 20)))
            return {
                "ok": bool(payload.get("ok")),
                "provider": canonical,
                "repository": target,
                "failed_jobs": list(payload.get("failed_jobs") or [])[:limit],
                "latest_failed_run": payload.get("latest_failed_run"),
                "error": payload.get("error"),
            }

        return {
            "ok": False,
            "provider": canonical,
            "error": "logs_not_supported_for_provider",
            "supported_log_providers": ["vercel", "railway", "github"],
        }

    result = _compute()
    if isinstance(result, dict) and result.get("ok"):
        cache_set(canonical, result, op="logs", target=f"{target}:{limit}", ttl_sec=_LOGS_TTL_SEC)
    return result


def provider_workflows(
    provider: str,
    *,
    repository: str = "",
    limit: int = 10,
    session_id: str = "default",
) -> dict[str, Any]:
    _ = session_id
    canonical = normalize_provider_name(provider)
    if not canonical:
        return {"ok": False, "error": "unknown_provider"}
    if canonical not in _WORKFLOW_PROVIDERS:
        return {
            "ok": False,
            "provider": canonical,
            "error": "workflows_not_supported_for_provider",
            "supported_workflow_providers": sorted(_WORKFLOW_PROVIDERS),
        }
    repo = str(repository or "").strip()
    if not repo:
        return {"ok": False, "error": "repository_required", "hint": "owner/repo e.g. pilotmain/AethOS"}

    token, err = resolve_provider_token("github")
    if not token:
        return {"ok": False, "provider": canonical, "error": err or "token_not_configured"}

    from aethos_core.providers.github.operations.workflow_runs_api import fetch_workflow_runs

    payload = fetch_workflow_runs(token, repository=repo, limit=max(1, min(limit, 25)))
    return {
        "ok": bool(payload.get("ok")),
        "provider": canonical,
        "workflows": payload,
        "error": payload.get("error"),
    }

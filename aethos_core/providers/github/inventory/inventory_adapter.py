# SPDX-License-Identifier: Apache-2.0
"""GitHub repository inventory adapter."""

from __future__ import annotations

from typing import Any

from aethos_core.providers.base.inventory_adapter import InventoryAdapter


class GitHubInventoryAdapter(InventoryAdapter):
    provider = "github"

    def fetch_projects_inventory(self, *, auth_context: dict[str, Any]) -> dict[str, Any]:
        token = str(auth_context.get("token") or "")
        if not token:
            return {"ok": False, "items": [], "error": "missing token"}
        from aethos_core.providers.github.api_client import list_repositories

        result = list_repositories(token)
        if not result.get("ok"):
            return {
                "ok": False,
                "items": [],
                "error": str(result.get("error") or "GitHub API request failed"),
            }
        rows: list[dict[str, Any]] = []
        for repo in result.get("repositories") or []:
            if not isinstance(repo, dict):
                continue
            visibility = "private" if repo.get("private") else "public"
            rows.append(
                {
                    "provider": "github",
                    "name": repo.get("name"),
                    "full_name": repo.get("full_name"),
                    "owner": repo.get("owner"),
                    "repo_id": repo.get("repo_id"),
                    "visibility": visibility,
                    "default_branch": repo.get("default_branch") or "—",
                    "html_url": repo.get("html_url") or "",
                    "updated_at": repo.get("updated_at") or "",
                    "evidence": ["source:github_api"],
                }
            )
        return {"ok": True, "items": rows, "error": None}

    def build_projects_inventory(self, *, auth_context: dict[str, Any]) -> list[dict[str, Any]]:
        fetched = self.fetch_projects_inventory(auth_context=auth_context)
        if not fetched.get("ok"):
            return []
        items = fetched.get("items")
        return items if isinstance(items, list) else []

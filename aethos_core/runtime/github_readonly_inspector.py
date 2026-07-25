# SPDX-License-Identifier: Apache-2.0
"""Run GitHub on-demand repository inventory jobs — API only, no operational memory writes."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from aethos_core.operations.execution.execution_evidence import CONFIDENCE_CONFIRMED, evidence_item
from aethos_core.providers.github.inventory.inventory_adapter import GitHubInventoryAdapter


class GitHubInventoryError(Exception):
    """Safe, operator-facing inventory failure (no token values)."""


@dataclass
class GitHubInventoryOutcome:
    summary: str
    preview: str
    full_result: str
    items: list[dict[str, Any]]
    evidence: list[dict[str, Any]]


def distinct_owner_logins(items: list[dict[str, Any]]) -> set[str]:
    owners: set[str] = set()
    for row in items:
        owner = str(row.get("owner") or "").strip()
        if owner and owner != "—":
            owners.add(owner)
    return owners


def build_chat_summary(items: list[dict[str, Any]]) -> str:
    if not items:
        return build_empty_inventory_summary()
    lines = ["GitHub repositories found:", ""]
    for row in items[:8]:
        full_name = str(row.get("full_name") or row.get("name") or "—")
        visibility = str(row.get("visibility") or "—")
        lines.append(f"- **{full_name}** — {visibility}")
    if len(items) > 8:
        lines.append("")
        lines.append(f"+ {len(items) - 8} more repositories — see Mission Control → Jobs for the full report.")
    lines.append("")
    owner_count = len(distinct_owner_logins(items)) or 1
    lines.append(
        f"Found **{len(items)}** repositor{'ies' if len(items) != 1 else 'y'} "
        f"across **{owner_count}** owner{'s' if owner_count != 1 else ''}."
    )
    return "\n".join(lines)


def build_empty_inventory_summary() -> str:
    return (
        "GitHub inventory completed, but no repositories were returned for this token.\n\n"
        "Check:\n"
        "- token scopes (repo read access)\n"
        "- account/org membership\n"
        "- GitHub API response"
    )


def build_inventory_error_summary(error: str) -> str:
    safe = (error or "GitHub API request failed").strip()[:240]
    return (
        "GitHub inventory could not retrieve repositories.\n\n"
        f"Reason:\n{safe}\n\n"
        "Check:\n"
        "- token validity\n"
        "- token scopes\n"
        "- GitHub API availability"
    )


def build_full_report(
    items: list[dict[str, Any]],
    *,
    user_request: str = "",
    inventory_error: str = "",
) -> str:
    owner_count = len(distinct_owner_logins(items))
    lines = [
        "# GitHub repositories inventory",
        "",
        f"**Repositories found:** {len(items)}",
        f"**Owners found:** {owner_count}",
        "",
        "| Repository | Owner | Visibility | Default branch |",
        "| --- | --- | --- | --- |",
    ]
    for row in items:
        full_name = str(row.get("full_name") or row.get("name") or "—")
        owner = str(row.get("owner") or "—")
        visibility = str(row.get("visibility") or "—")
        branch = str(row.get("default_branch") or "—")
        lines.append(f"| {full_name} | {owner} | {visibility} | `{branch}` |")
    if not items:
        lines.append("| (none) | — | — | — |")
    lines.extend(["", "## Evidence", "", "- source:github_api · confidence: confirmed"])
    if inventory_error:
        lines.extend(["", "## Diagnostic", "", f"- {inventory_error.strip()[:500]}"])
    if user_request:
        lines.extend(["", f"_Request:_ {user_request[:500]}"])
    return "\n".join(lines)


def run_github_repositories_inventory(
    *,
    credential_id: str,
    user_request: str = "",
) -> GitHubInventoryOutcome:
    from aethos_core.providers.github.auth import GitHubAuthAdapter

    token = GitHubAuthAdapter().get_api_token(credential_id)
    if not token:
        raise GitHubInventoryError("GitHub API token unavailable for inventory.")

    fetched = GitHubInventoryAdapter().fetch_projects_inventory(auth_context={"token": token})
    if not fetched.get("ok"):
        error = str(fetched.get("error") or "GitHub API request failed")
        summary = build_inventory_error_summary(error)
        build_full_report([], user_request=user_request, inventory_error=error)
        raise GitHubInventoryError(summary)

    items = fetched.get("items") if isinstance(fetched.get("items"), list) else []
    summary = build_chat_summary(items)
    full = build_full_report(items, user_request=user_request)
    evidence = [
        evidence_item(
            source="github_api",
            type="inventory",
            confidence=CONFIDENCE_CONFIRMED,
            message=f"Listed {len(items)} GitHub repositor{'ies' if len(items) != 1 else 'y'} via REST API.",
            service_count=len(items),
        )
    ]
    if items:
        for row in items[:8]:
            full_name = str(row.get("full_name") or row.get("name") or "")
            if full_name:
                evidence.append(
                    evidence_item(
                        source="github_api",
                        type="repository",
                        confidence=CONFIDENCE_CONFIRMED,
                        message=f"Repository `{full_name}` ({row.get('visibility') or 'unknown'}).",
                        service_id=row.get("repo_id"),
                        project_id=row.get("owner"),
                    )
                )
    return GitHubInventoryOutcome(
        summary=summary,
        preview=summary.split("\n")[0][:240],
        full_result=full,
        items=items,
        evidence=evidence,
    )

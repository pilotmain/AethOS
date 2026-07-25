# SPDX-License-Identifier: Apache-2.0
"""Repository rename / transfer reconciliation across binding layers."""

from __future__ import annotations

import re
import subprocess
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

from aethos_core.provider_topology.github_access_verifier import list_accessible_github_repos, verify_github_repo_access
from aethos_core.provider_topology.topology_memory import get_binding
from aethos_core.providers.github.api_client import parse_owner_repo, request_github


@dataclass
class RepoRemoteInfo:
    path: str
    remote_name: str = "origin"
    remote_url: str = ""
    owner_repo: str | None = None
    ok: bool = False
    message: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "path": self.path,
            "remote_name": self.remote_name,
            "remote_url": self.remote_url,
            "owner_repo": self.owner_repo,
            "ok": self.ok,
            "message": self.message,
        }


@dataclass
class RepoRedirectResult:
    old_repo: str
    redirected: bool = False
    current_repo: str | None = None
    detection_source: str = "none"
    old_accessible: bool = False
    current_accessible: bool = False
    message: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "old_repo": self.old_repo,
            "redirected": self.redirected,
            "current_repo": self.current_repo,
            "detection_source": self.detection_source,
            "old_accessible": self.old_accessible,
            "current_accessible": self.current_accessible,
            "message": self.message,
        }


@dataclass
class RailwaySourceMetadata:
    service_name: str
    project: str
    environment: str
    linked_repo: str | None = None
    source: str = "unknown"
    stale: bool = False
    message: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "service_name": self.service_name,
            "project": self.project,
            "environment": self.environment,
            "linked_repo": self.linked_repo,
            "source": self.source,
            "stale": self.stale,
            "message": self.message,
        }


@dataclass
class ReconciliationLayer:
    layer: str
    repo: str | None = None
    stale: bool = False
    verified: bool = False
    message: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "layer": self.layer,
            "repo": self.repo,
            "stale": self.stale,
            "verified": self.verified,
            "message": self.message,
        }


@dataclass
class ReconciliationResult:
    provider: str
    project: str
    environment: str
    service_name: str
    old_repo: str
    candidate_repo: str | None = None
    confirmed_repo: str | None = None
    layers: list[ReconciliationLayer] = field(default_factory=list)
    railway_metadata: RailwaySourceMetadata | None = None
    local_remote: RepoRemoteInfo | None = None
    redirect: RepoRedirectResult | None = None
    stale_locations: list[str] = field(default_factory=list)
    recommended_action: str = ""
    can_auto_update: bool = False
    updated: bool = False
    message: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "provider": self.provider,
            "project": self.project,
            "environment": self.environment,
            "service_name": self.service_name,
            "old_repo": self.old_repo,
            "candidate_repo": self.candidate_repo,
            "confirmed_repo": self.confirmed_repo,
            "layers": [layer.to_dict() for layer in self.layers],
            "railway_metadata": self.railway_metadata.to_dict() if self.railway_metadata else None,
            "local_remote": self.local_remote.to_dict() if self.local_remote else None,
            "redirect": self.redirect.to_dict() if self.redirect else None,
            "stale_locations": list(self.stale_locations),
            "recommended_action": self.recommended_action,
            "can_auto_update": self.can_auto_update,
            "updated": self.updated,
            "message": self.message,
        }


_GITHUB_REMOTE_RX = re.compile(
    r"(?:github\.com[/:]|git@github\.com:)([a-z0-9][a-z0-9._-]*)/([a-z0-9][a-z0-9._-]*?)(?:\.git)?/?$",
    re.I,
)


def read_local_git_remote(path: str, *, remote_name: str = "origin") -> RepoRemoteInfo:
    root = Path(path or "").expanduser().resolve()
    if not root.is_dir():
        return RepoRemoteInfo(path=str(path), remote_name=remote_name, message="Local path does not exist.")

    git_dir = root / ".git"
    if not git_dir.exists():
        return RepoRemoteInfo(path=str(root), remote_name=remote_name, message="Not a git repository.")

    try:
        proc = subprocess.run(
            ["git", "-C", str(root), "remote", "get-url", remote_name],
            capture_output=True,
            text=True,
            timeout=5,
            check=False,
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        return RepoRemoteInfo(path=str(root), remote_name=remote_name, message=str(exc))

    if proc.returncode != 0:
        return RepoRemoteInfo(
            path=str(root),
            remote_name=remote_name,
            message=(proc.stderr or proc.stdout or "git remote unavailable.").strip(),
        )

    remote_url = (proc.stdout or "").strip()
    owner_repo = _owner_repo_from_remote_url(remote_url)
    return RepoRemoteInfo(
        path=str(root),
        remote_name=remote_name,
        remote_url=remote_url,
        owner_repo=owner_repo,
        ok=bool(owner_repo),
        message=f"Local git remote `{remote_name}` resolved to {owner_repo}." if owner_repo else "Could not parse owner/repo from remote URL.",
    )


def detect_repo_redirect(
    old_repo: str,
    *,
    accessible_repos: list[str] | None = None,
) -> RepoRedirectResult:
    repo = (old_repo or "").strip()
    if not repo or "/" not in repo:
        return RepoRedirectResult(old_repo=repo, message="Invalid repository name.")

    old_access = verify_github_repo_access(repo, accessible_repos=accessible_repos)
    if old_access.ok:
        return RepoRedirectResult(
            old_repo=repo,
            redirected=False,
            current_repo=repo,
            detection_source="github_installation",
            old_accessible=True,
            current_accessible=True,
            message=f"Repository `{repo}` is still accessible.",
        )

    redirect = _detect_github_api_redirect(repo)
    if redirect:
        current_access = verify_github_repo_access(redirect, accessible_repos=accessible_repos)
        return RepoRedirectResult(
            old_repo=repo,
            redirected=True,
            current_repo=redirect,
            detection_source="github_api_redirect",
            old_accessible=False,
            current_accessible=current_access.ok,
            message=f"GitHub redirect detected: `{repo}` → `{redirect}`.",
        )

    owner, name = parse_owner_repo(repo)
    repos = accessible_repos if accessible_repos is not None else list_accessible_github_repos()
    match = _find_repo_name_match(name, repos or [], exclude_owner=owner)
    if match:
        current_access = verify_github_repo_access(match, accessible_repos=repos)
        return RepoRedirectResult(
            old_repo=repo,
            redirected=True,
            current_repo=match,
            detection_source="accessible_repo_match",
            old_accessible=False,
            current_accessible=current_access.ok,
            message=f"Accessible repository match found: `{match}` (same repo name, new owner).",
        )

    return RepoRedirectResult(
        old_repo=repo,
        redirected=False,
        old_accessible=False,
        current_accessible=False,
        message=f"No redirect or accessible replacement found for `{repo}`.",
    )


def read_railway_service_source_metadata(
    *,
    project: str,
    environment: str,
    service_name: str,
    service_id: str | None = None,
    expected_repo: str | None = None,
) -> RailwaySourceMetadata:
    linked_repo = None
    source = "unknown"
    message = "Railway source metadata unavailable."

    try:
        from aethos_core.provider_discovery import get_provider_inventory

        inventory = get_provider_inventory("railway")
        if inventory is not None:
            for row in inventory.all_services():
                if (
                    str(row.get("project_name") or "") == project
                    and str(row.get("environment") or "production") == environment
                    and str(row.get("service_name") or "") == service_name
                ):
                    linked_repo = str(row.get("known_repo") or row.get("github_repo") or row.get("git_repo") or "").strip() or None
                    source = "provider_inventory"
                    message = "Read Railway service metadata from provider inventory."
                    break
    except Exception:
        pass

    if not linked_repo and service_id:
        linked_repo = _railway_deployment_repo(service_id)
        if linked_repo:
            source = "deployment_meta"
            message = "Read Railway deployment source metadata."

    stale = bool(
        expected_repo
        and linked_repo
        and linked_repo.lower() != expected_repo.lower()
    )
    if linked_repo and expected_repo and stale:
        message = (
            f"Railway appears linked to `{linked_repo}`, but AethOS expects `{expected_repo}`."
        )
    elif linked_repo:
        message = f"Railway service source metadata: `{linked_repo}`."

    return RailwaySourceMetadata(
        service_name=service_name,
        project=project,
        environment=environment,
        linked_repo=linked_repo,
        source=source,
        stale=stale,
        message=message,
    )


def reconcile_source_binding(
    *,
    provider: str = "railway",
    project: str,
    environment: str,
    service_name: str,
    old_repo: str,
    candidate_repo: str | None = None,
    local_path: str | None = None,
    session_id: str | None = None,
    accessible_repos: list[str] | None = None,
) -> ReconciliationResult:
    provider = (provider or "railway").strip().lower()
    old_repo = (old_repo or "").strip()
    binding = get_binding(provider=provider, project=project, environment=environment, service_name=service_name)
    service_id = binding.service_id if binding else None

    layers: list[ReconciliationLayer] = []
    stale_locations: list[str] = []

    workspace = local_path or _default_local_repo_path()
    local_remote = read_local_git_remote(workspace) if workspace else None
    if local_remote and local_remote.ok and local_remote.owner_repo:
        stale = bool(old_repo and local_remote.owner_repo.lower() != old_repo.lower())
        if stale and local_remote.owner_repo.lower() != old_repo.lower() and local_remote.owner_repo != candidate_repo:
            stale_locations.append("local_git_remote")
        layers.append(
            ReconciliationLayer(
                layer="local_git_remote",
                repo=local_remote.owner_repo,
                stale=stale and local_remote.owner_repo.lower() != old_repo.lower(),
                verified=True,
                message=local_remote.message,
            )
        )

    redirect = detect_repo_redirect(old_repo, accessible_repos=accessible_repos)
    if redirect.current_repo:
        layers.append(
            ReconciliationLayer(
                layer="github_redirect",
                repo=redirect.current_repo,
                stale=redirect.redirected,
                verified=redirect.current_accessible,
                message=redirect.message,
            )
        )

    confirmed = candidate_repo or redirect.current_repo or (local_remote.owner_repo if local_remote and local_remote.ok else None)
    railway = read_railway_service_source_metadata(
        project=project,
        environment=environment,
        service_name=service_name,
        service_id=service_id,
        expected_repo=confirmed or old_repo,
    )
    if railway.linked_repo:
        layers.append(
            ReconciliationLayer(
                layer="railway_service_metadata",
                repo=railway.linked_repo,
                stale=railway.stale,
                verified=not railway.stale,
                message=railway.message,
            )
        )
        if railway.stale:
            stale_locations.append("railway_service_metadata")

    stored_repo = binding.github_repo if binding else old_repo
    topology_stale = bool(confirmed and stored_repo and stored_repo.lower() != confirmed.lower())
    layers.append(
        ReconciliationLayer(
            layer="provider_topology_binding",
            repo=stored_repo,
            stale=topology_stale,
            verified=bool(binding and binding.source_verified and not topology_stale),
            message="Canonical provider topology binding.",
        )
    )
    if topology_stale:
        stale_locations.append("provider_topology_binding")

    if confirmed:
        access = verify_github_repo_access(confirmed, accessible_repos=accessible_repos)
        layers.append(
            ReconciliationLayer(
                layer="github_installation_access",
                repo=confirmed,
                stale=not access.ok,
                verified=access.ok,
                message=access.message,
            )
        )
        if not access.ok:
            stale_locations.append("github_installation_access")

    can_auto_update = bool(
        confirmed
        and confirmed.lower() != old_repo.lower()
        and verify_github_repo_access(confirmed, accessible_repos=accessible_repos).ok
    )

    recommended = _recommended_action(
        old_repo=old_repo,
        confirmed=confirmed,
        stale_locations=stale_locations,
        railway=railway,
        can_auto_update=can_auto_update,
    )

    return ReconciliationResult(
        provider=provider,
        project=project,
        environment=environment,
        service_name=service_name,
        old_repo=old_repo,
        candidate_repo=candidate_repo or redirect.current_repo,
        confirmed_repo=confirmed,
        layers=layers,
        railway_metadata=railway,
        local_remote=local_remote,
        redirect=redirect,
        stale_locations=stale_locations,
        recommended_action=recommended,
        can_auto_update=can_auto_update,
        message=_compose_summary(old_repo=old_repo, confirmed=confirmed, stale_locations=stale_locations, railway=railway),
    )


def refresh_binding_from_remote(
    *,
    provider: str = "railway",
    project: str,
    environment: str,
    service_name: str,
    local_path: str | None = None,
    confirm: bool = False,
    accessible_repos: list[str] | None = None,
) -> ReconciliationResult:
    binding = get_binding(provider=provider, project=project, environment=environment, service_name=service_name)
    old_repo = str(binding.github_repo if binding and binding.github_repo else "")
    local_remote = read_local_git_remote(local_path or _default_local_repo_path() or "")
    candidate = local_remote.owner_repo if local_remote and local_remote.ok else None

    result = reconcile_source_binding(
        provider=provider,
        project=project,
        environment=environment,
        service_name=service_name,
        old_repo=old_repo,
        candidate_repo=candidate,
        local_path=local_path,
        accessible_repos=accessible_repos,
    )

    if confirm and result.can_auto_update and result.confirmed_repo:
        from aethos_core.provider_topology.binding_update_flow import apply_binding_update

        apply_binding_update(
            provider=provider,
            project=project,
            environment=environment,
            service_name=service_name,
            github_repo=result.confirmed_repo,
            service_id=binding.service_id if binding else None,
        )
        result.updated = True
        result.message = (
            f"Updated canonical binding for **{project} / {environment} / {service_name}** "
            f"to **{result.confirmed_repo}**."
        )
    return result


def compose_reconciliation_reply(result: ReconciliationResult) -> str:
    lines = [
        "I checked repository transfer/rename sources across AethOS binding layers.",
        "",
        f"Service: **{result.project} / {result.environment} / {result.service_name}**",
        f"Old repo: **{result.old_repo or '(none)'}**",
    ]
    if result.confirmed_repo and result.confirmed_repo.lower() != (result.old_repo or "").lower():
        lines.append(f"Current repo candidate: **{result.confirmed_repo}**")
    lines.append("")
    lines.append("Layer checks:")
    for layer in result.layers:
        flag = "stale" if layer.stale else "ok"
        repo = layer.repo or "(none)"
        lines.append(f"- **{layer.layer}** [{flag}]: `{repo}` — {layer.message}")
    if result.railway_metadata and result.railway_metadata.stale and result.railway_metadata.linked_repo:
        lines.extend(
            [
                "",
                "Railway note:",
                (
                    f"The local/AethOS binding may be updated, but Railway itself still appears linked to "
                    f"**{result.railway_metadata.linked_repo}**. Update the Railway service source connection to "
                    f"**{result.confirmed_repo or result.candidate_repo or 'the current repo'}** or reconnect the GitHub app."
                ),
            ]
        )
    if result.stale_locations:
        lines.extend(["", "Stale binding locations:", *[f"- {loc}" for loc in result.stale_locations]])
    lines.extend(["", "Next recommended action:", f"- {result.recommended_action}"])
    return "\n".join(lines)


def suggest_repo_from_transfer(
    old_repo: str,
    *,
    accessible_repos: list[str] | None = None,
) -> str | None:
    redirect = detect_repo_redirect(old_repo, accessible_repos=accessible_repos)
    if redirect.current_repo and redirect.current_repo.lower() != old_repo.lower() and redirect.current_accessible:
        return redirect.current_repo
    return None


def _default_local_repo_path() -> str | None:
    root = Path(__file__).resolve().parents[2]
    if (root / ".git").exists():
        return str(root)
    return None


def _owner_repo_from_remote_url(remote_url: str) -> str | None:
    url = (remote_url or "").strip()
    if not url:
        return None
    match = _GITHUB_REMOTE_RX.search(url.replace("ssh://", ""))
    if match:
        return f"{match.group(1)}/{match.group(2)}"
    parsed = urlparse(url)
    if parsed.path and parsed.path.count("/") >= 2:
        parts = [p for p in parsed.path.split("/") if p]
        if len(parts) >= 2:
            owner, repo = parts[0], parts[1]
            if repo.endswith(".git"):
                repo = repo[:-4]
            return f"{owner}/{repo}"
    return None


def _detect_github_api_redirect(old_repo: str) -> str | None:
    owner, repo = parse_owner_repo(old_repo)
    if not owner or not repo:
        return None
    try:
        from aethos_core.providers.github.auth import GitHubAuthAdapter

        auth = GitHubAuthAdapter().resolve_best_auth_method(operation="read_repos")
        credential_id = auth.get("credential_id")
        if not credential_id:
            return None
        token = GitHubAuthAdapter().get_api_token(str(credential_id))
    except Exception:
        return None

    response = request_github(token, "GET", f"/repos/{owner}/{repo}")
    if response.get("ok"):
        data = response.get("data")
        if isinstance(data, dict):
            full_name = str(data.get("full_name") or "")
            if full_name and full_name.lower() != old_repo.lower():
                return full_name
            if full_name:
                return full_name
        return None

    status = response.get("http_status")
    if status == 404:
        repos = list_accessible_github_repos() or []
        return _find_repo_name_match(repo, repos, exclude_owner=owner)
    return None


def _find_repo_name_match(name: str, repos: list[str], *, exclude_owner: str | None = None) -> str | None:
    norm = (name or "").strip().lower()
    if not norm:
        return None
    matches = []
    for repo in repos:
        owner, repo_name = parse_owner_repo(repo)
        if repo_name.lower() != norm:
            continue
        if exclude_owner and owner.lower() == exclude_owner.lower():
            continue
        matches.append(repo)
    if len(matches) == 1:
        return matches[0]
    return None


def _railway_deployment_repo(service_id: str) -> str | None:
    try:
        from aethos_core.providers.railway.mutations import resolve_railway_mutation_credentials

        token, _, err = resolve_railway_mutation_credentials()
        if not token or err:
            return None
        from aethos_core.providers.railway.api_client import graphql_query

        out = graphql_query(
            token,
            """
            query ServiceSource($serviceId: String!) {
              service(id: $serviceId) {
                id
                name
                deployments(first: 1) {
                  edges {
                    node {
                      meta
                    }
                  }
                }
              }
            }
            """,
            {"serviceId": service_id},
        )
        if not out.get("ok"):
            return None
        service = ((out.get("data") or {}).get("service") or {})
        edges = (((service.get("deployments") or {}).get("edges")) or [])
        if not edges:
            return None
        node = (edges[0] or {}).get("node") or {}
        meta = node.get("meta") or {}
        if not isinstance(meta, dict):
            return None
        for key in ("repo", "repository", "githubRepo", "github_repo", "gitHubRepo"):
            val = meta.get(key)
            if isinstance(val, str) and "/" in val:
                return val
            if isinstance(val, dict):
                full = val.get("full_name") or val.get("fullName")
                if isinstance(full, str) and "/" in full:
                    return full
        return None
    except Exception:
        return None


def _recommended_action(
    *,
    old_repo: str,
    confirmed: str | None,
    stale_locations: list[str],
    railway: RailwaySourceMetadata,
    can_auto_update: bool,
) -> str:
    if can_auto_update and confirmed:
        return f"Confirm updating AethOS source binding from `{old_repo}` to `{confirmed}`, then retry the governed operation."
    if "railway_service_metadata" in stale_locations and railway.linked_repo and confirmed:
        return (
            f"Update Railway service source connection from `{railway.linked_repo}` to `{confirmed}` "
            "or reconnect the GitHub app, then retry."
        )
    if "local_git_remote" in stale_locations and confirmed:
        return (
            f"Update local git remote: `git remote set-url origin git@github.com:{confirmed}.git`, "
            "then refresh AethOS binding."
        )
    if confirmed:
        return f"Verify GitHub installation access for `{confirmed}` and refresh provider topology."
    return "Provide the current owner/repo or reconnect GitHub/Railway source metadata."


def _compose_summary(
    *,
    old_repo: str,
    confirmed: str | None,
    stale_locations: list[str],
    railway: RailwaySourceMetadata,
) -> str:
    if confirmed and confirmed.lower() != old_repo.lower():
        where = ", ".join(stale_locations) if stale_locations else "no stale layers detected"
        return f"Repository appears to have moved from `{old_repo}` to `{confirmed}` ({where})."
    if railway.stale and railway.linked_repo:
        return f"Railway still references `{railway.linked_repo}` while AethOS expects `{confirmed or old_repo}`."
    return f"No confirmed repository transfer detected for `{old_repo}`."

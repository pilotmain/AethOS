# SPDX-License-Identifier: Apache-2.0
"""Unified deployment target resolution for greenfield and autonomous flows."""

from __future__ import annotations

import json
import re
from time import time
from typing import Any

from aethos_core.deployment_targets.bindings import resolve_bound_target
from aethos_core.deployment_targets.paths import session_deploy_targets_path
from aethos_core.deployment_targets.registry import (
    find_target_by_alias,
    find_target_by_repo,
    find_target_by_workspace_id,
    match_aliases_in_text,
    target_to_resolution,
)
from aethos_core.providers.railway.deployment_plan.deployment_plan_artifact import parse_plan_fields_from_text
from aethos_core.providers.railway.deployment_readiness.deployment_readiness_checks import extract_github_repo_target
from aethos_core.providers.railway.greenfield_deployment.git_remote_resolution import normalize_github_repository_slug

_REPO_SLUG_RX = re.compile(r"\b([a-z0-9][a-z0-9._-]+/[a-z0-9][a-z0-9._-]+)\b", re.I)
_BARE_DEPLOY_NAME_RX = re.compile(
    r"\b(?:deploye?|deploy(?:ment)?|redeploy)\s+([a-z0-9][a-z0-9._-]+)\b",
    re.I,
)
_BARE_NAME_STOPWORDS = frozenset(
    {
        "vercel",
        "railway",
        "github",
        "docker",
        "kubernetes",
        "aws",
        "gcp",
        "azure",
        "the",
        "this",
        "that",
        "my",
        "our",
        "a",
        "an",
        "new",
        "fresh",
        "existing",
        "current",
        "local",
        "remote",
        "from",
        "and",
        "with",
        "set",
        "up",
        "env",
        "vars",
        "variables",
        "to",
        "on",
        "in",
        "for",
        "into",
    }
)
_SESSION_TARGET_TTL_SECONDS = 7200
_SESSION_TARGET_MEMORY: dict[str, dict[str, Any]] = {}


def resolve_deployment_target(
    user_text: str,
    *,
    session_id: str = "default",
    workspace_hint: str = "",
    user_id: str = "",
    channel: str = "web",
) -> dict[str, Any]:
    """Resolve deploy target: chat repo → registry alias → binding → local workspace → git remote."""
    text = (user_text or "").strip()
    hint = (workspace_hint or "").strip()

    from aethos_core.local_workspace.portfolio import extract_filesystem_paths, resolve_repo_reference

    if extract_filesystem_paths(text):
        ref = resolve_repo_reference(text, session_id=session_id)
        ref_path = str(ref.get("resolved_path") or ref.get("path") or "").strip()
        if ref_path and str(ref.get("source") or "") in {
            "portfolio_path",
            "portfolio_name",
            "portfolio_name_partial",
            "portfolio_remote",
            "portfolio_child_path",
            "chat_path",
            "registered",
            "session_active",
            "cwd_prefix",
        }:
            git = _git_resolution_from_path(ref_path)
            if git.get("ok"):
                git["local_path"] = ref_path
                git["source"] = f"portfolio_{ref.get('source')}" if "portfolio" in str(ref.get("source")) else str(ref.get("source"))
                git["branch"] = _resolve_branch(text, git.get("branch") or "main")
                return git

    explicit_repo = _resolve_explicit_repo(text)
    if explicit_repo:
        row = find_target_by_repo(explicit_repo)
        if row:
            resolved = target_to_resolution(row, source="registry_repo")
            resolved["branch"] = _resolve_branch(text, resolved.get("branch") or "main")
            _save_session_deploy_target(
                session_id,
                repo=explicit_repo,
                repo_hint=explicit_repo.split("/")[-1],
                flow="railway_greenfield",
                status="resolved",
                user_text=text,
            )
            return resolved
        resolved = _repo_only_resolution(explicit_repo, text, source="chat_repo")
        _save_session_deploy_target(
            session_id,
            repo=explicit_repo,
            repo_hint=explicit_repo.split("/")[-1],
            flow="railway_greenfield",
            status="resolved",
            user_text=text,
        )
        return resolved

    alias_row = match_aliases_in_text(text) or (find_target_by_alias(hint) if hint else None)
    if alias_row:
        resolved = target_to_resolution(alias_row, source="registry_alias")
        resolved["branch"] = _resolve_branch(text, resolved.get("branch") or "main")
        repo = str(resolved.get("repo") or "")
        if repo:
            _save_session_deploy_target(
                session_id,
                repo=repo,
                repo_hint=repo.split("/")[-1],
                flow="railway_greenfield",
                status="resolved",
                user_text=text,
            )
        return resolved

    bare_name = _extract_bare_repo_name_from_text(text)
    if bare_name:
        inventory = _resolve_bare_repo_via_github_inventory(bare_name)
        _save_session_deploy_target(
            session_id,
            repo_hint=bare_name,
            repo=str(inventory.get("repo") or ""),
            flow="railway_greenfield",
            status="resolved" if inventory.get("ok") else "awaiting_resolution",
            user_text=text,
            inventory_status=str(inventory.get("blocker_code") or ""),
        )
        if inventory.get("ok"):
            repo = normalize_github_repository_slug(str(inventory["repo"]))
            row = find_target_by_repo(repo)
            if row:
                resolved = target_to_resolution(row, source="registry_repo")
                resolved["branch"] = _resolve_branch(text, resolved.get("branch") or "main")
                return resolved
            return _repo_only_resolution(repo, text, source=str(inventory.get("source") or "github_inventory"))
        return _inventory_resolution_failure(bare_name, inventory)

    session_target = get_session_deploy_target(session_id)
    if session_target and not _text_names_new_deploy_target(text):
        session_repo = normalize_github_repository_slug(str(session_target.get("repo") or ""))
        if session_repo:
            row = find_target_by_repo(session_repo)
            if row:
                resolved = target_to_resolution(row, source="registry_repo")
                resolved["branch"] = _resolve_branch(text, resolved.get("branch") or "main")
                return resolved
            return _repo_only_resolution(session_repo, text, source="session_deploy_target")
        session_hint = str(session_target.get("repo_hint") or "").strip()
        if session_hint:
            inventory = _resolve_bare_repo_via_github_inventory(session_hint)
            if inventory.get("ok"):
                repo = normalize_github_repository_slug(str(inventory["repo"]))
                _save_session_deploy_target(
                    session_id,
                    repo_hint=session_hint,
                    repo=repo,
                    flow="railway_greenfield",
                    status="resolved",
                    user_text=text,
                )
                row = find_target_by_repo(repo)
                if row:
                    resolved = target_to_resolution(row, source="registry_repo")
                    resolved["branch"] = _resolve_branch(text, resolved.get("branch") or "main")
                    return resolved
                return _repo_only_resolution(repo, text, source="session_github_inventory")
            return _inventory_resolution_failure(session_hint, inventory)

    bound = resolve_bound_target(session_id=session_id, user_id=user_id, channel=channel)
    if bound:
        bound["branch"] = _resolve_branch(text, bound.get("branch") or "main")
        return bound

    local = _resolve_from_local_workspace(session_id=session_id, hint=hint)
    if local.get("ok"):
        return local

    return {
        "ok": False,
        "blocker_code": "DEPLOYMENT_TARGET_UNRESOLVED",
        "detail": "Could not determine deployment target.",
        "safe_next_command": (
            'Register a deployment target in Mission Control → Deployment Targets, '
            'or specify owner/repo in chat (e.g. "deploy acme/widget to Vercel").'
        ),
    }


def get_session_deploy_target(session_id: str) -> dict[str, Any] | None:
    """Return the active deploy target for this chat session, if any."""
    sid = (session_id or "default").strip() or "default"
    cached = _SESSION_TARGET_MEMORY.get(sid)
    if cached is None:
        index = _load_session_target_index()
        raw = index.get("sessions", {}).get(sid)
        if isinstance(raw, dict):
            cached = dict(raw)
            _SESSION_TARGET_MEMORY[sid] = cached
    if not cached:
        return None
    expires_at = float(cached.get("expires_at") or 0)
    if expires_at and time() > expires_at:
        clear_session_deploy_target(sid)
        return None
    return cached


def clear_session_deploy_target(session_id: str) -> None:
    sid = (session_id or "default").strip() or "default"
    _SESSION_TARGET_MEMORY.pop(sid, None)
    index = _load_session_target_index()
    sessions = dict(index.get("sessions") or {})
    if sid in sessions:
        sessions.pop(sid, None)
        index["sessions"] = sessions
        index["updated_at"] = time()
        _atomic_write_session_index(index)


def clear_session_deploy_targets_for_tests() -> None:
    _SESSION_TARGET_MEMORY.clear()
    path = session_deploy_targets_path()
    if path.is_file():
        path.unlink()


def is_railway_greenfield_deploy_continuation(text: str, *, session_id: str = "default") -> bool:
    """True when a follow-up should continue an in-progress Railway greenfield deploy."""
    pending = get_session_deploy_target(session_id)
    if not pending or str(pending.get("flow") or "") != "railway_greenfield":
        return False
    raw = (text or "").strip()
    if not raw:
        return False
    if _text_names_new_deploy_target(raw):
        return False
    if _BARE_DEPLOY_NAME_RX.search(raw) and _extract_bare_repo_name_from_text(raw):
        return False
    continuation_rx = re.compile(
        r"\b("
        r"connected"
        r"|already"
        r"|proceed"
        r"|continue"
        r"|go\s+ahead"
        r"|it(?:'|)s\s+connected"
        r"|repo\s+is\s+connected"
        r"|github\s+repo"
        r"|yes"
        r")\b",
        re.I,
    )
    if continuation_rx.search(raw):
        return True
    if pending.get("status") == "awaiting_resolution" and len(raw) <= 160:
        return True
    return False


def merge_greenfield_deploy_continuation_text(text: str, *, session_id: str = "default") -> str:
    """Rehydrate the original deploy request so follow-ups keep the named repo."""
    pending = get_session_deploy_target(session_id)
    if not pending:
        return text
    raw = (text or "").strip()
    repo_hint = str(pending.get("repo_hint") or pending.get("repo") or "").strip()
    if not repo_hint:
        return raw
    if repo_hint in raw or ("/" in repo_hint and repo_hint in raw):
        return raw
    original = str(pending.get("user_text") or "").strip()
    if original and repo_hint in original.lower():
        return f"{original} {raw}".strip()
    return f"deploy {repo_hint} to railway {raw}".strip()


def resolve_workspace_hint_for_session(
    explicit_hint: str | None,
    *,
    session_id: str = "default",
    cwd: str | None = None,
) -> str:
    """Layered workspace hint: explicit → session active → cwd prefix → binding alias → sole registry → aethos."""
    from aethos_core.local_workspace.registry import list_workspaces
    from aethos_core.local_workspace.session_context import (
        get_active_workspace,
        resolve_workspace_by_cwd_prefix,
    )

    if explicit_hint and explicit_hint.strip():
        hint = explicit_hint.strip()
        if hint.startswith("/"):
            return hint
        return hint

    active = get_active_workspace(session_id)
    if active and active.get("name"):
        return str(active["name"])

    cwd_row = resolve_workspace_by_cwd_prefix(cwd)
    if cwd_row and cwd_row.get("name"):
        return str(cwd_row["name"])

    bound = resolve_bound_target(session_id=session_id)
    if bound and bound.get("alias"):
        return str(bound["alias"])

    rows = list_workspaces()
    if len(rows) == 1 and rows[0].get("name"):
        return str(rows[0]["name"])

    return "aethos"


def format_deployment_target_resolution(resolved: dict[str, Any]) -> str:
    if not resolved.get("ok"):
        return (
            f"**Deployment target unavailable** (`{resolved.get('blocker_code')}`)\n\n"
            f"- Detail: {resolved.get('detail')}\n\n"
            f"**Required action:** {resolved.get('safe_next_command')}"
        )
    lines = [
        "**Deployment target**",
        "",
        f"- Source: `{resolved.get('source')}`",
        f"- Repository: `{resolved.get('repo')}` @ `{resolved.get('branch')}`",
    ]
    if resolved.get("alias"):
        lines.append(f"- Alias: `{resolved.get('alias')}`")
    if resolved.get("vercel_project"):
        lines.append(f"- Vercel project: `{resolved.get('vercel_project')}`")
    if resolved.get("railway_project"):
        lines.append(f"- Railway project: `{resolved.get('railway_project')}`")
    if resolved.get("root_directory"):
        lines.append(f"- Root directory: `{resolved.get('root_directory')}`")
    return "\n".join(lines)


def _resolve_explicit_repo(text: str) -> str:
    parsed = parse_plan_fields_from_text(text, default_repo="")
    repo = normalize_github_repository_slug(str(parsed.get("repo") or extract_github_repo_target(text) or ""))
    if repo:
        return repo
    slug_match = _REPO_SLUG_RX.search(text or "")
    if slug_match:
        return normalize_github_repository_slug(slug_match.group(1))
    return ""


def _resolve_branch(text: str, fallback: str) -> str:
    parsed = parse_plan_fields_from_text(text, default_repo="")
    branch = str(parsed.get("branch") or "").strip()
    return branch or fallback or "main"


def _repo_only_resolution(repo: str, text: str, *, source: str) -> dict[str, Any]:
    branch = _resolve_branch(text, "main")
    basename = repo.split("/")[-1] if "/" in repo else repo
    return {
        "ok": True,
        "source": source,
        "target_id": "",
        "alias": basename,
        "repo": repo,
        "branch": branch,
        "project_name": basename,
        "vercel_project": basename,
        "railway_project": "",
        "railway_service": "",
        "railway_environment": "",
        "root_directory": "",
        "default_provider": "",
        "workspace_id": "",
        "local_path": "",
    }


def _git_resolution_from_path(path: str) -> dict[str, Any]:
    from aethos_core.providers.railway.greenfield_deployment.git_remote_resolution import (
        normalize_github_repository_slug,
        resolve_git_remote_from_workspace,
    )

    git_remote = resolve_git_remote_from_workspace(path)
    if not git_remote.get("ok"):
        return {"ok": False}
    repo = normalize_github_repository_slug(str(git_remote.get("repository") or ""))
    if not repo:
        return {"ok": False}
    basename = repo.split("/")[-1]
    row = find_target_by_repo(repo)
    if row:
        resolved = target_to_resolution(row, source="registry_repo")
        resolved["branch"] = str(git_remote.get("branch") or resolved.get("branch") or "main")
        resolved["local_path"] = path
        return resolved
    return {
        "ok": True,
        "source": "local_path",
        "target_id": "",
        "alias": basename,
        "repo": repo,
        "branch": str(git_remote.get("branch") or "main"),
        "project_name": str(git_remote.get("project_name") or basename),
        "vercel_project": basename,
        "railway_project": "",
        "railway_service": "",
        "railway_environment": "",
        "root_directory": "",
        "default_provider": "",
        "workspace_id": "",
        "local_path": path,
    }


def _resolve_from_local_workspace(*, session_id: str, hint: str) -> dict[str, Any]:
    from aethos_core.local_workspace.registry import find_workspace_by_hint
    from aethos_core.local_workspace.session_context import get_active_workspace
    from aethos_core.providers.railway.greenfield_deployment.git_remote_resolution import (
        normalize_github_repository_slug,
        resolve_git_remote_from_workspace,
    )

    workspace_row: dict[str, Any] | None = None
    active = get_active_workspace(session_id)
    if active:
        workspace_row = active
        wid = str(active.get("workspace_id") or "")
        linked = find_target_by_workspace_id(wid) if wid else None
        if linked:
            resolved = target_to_resolution(linked, source="registry_workspace")
            return resolved

    if hint:
        workspace_row = find_workspace_by_hint(hint) or workspace_row

    if not workspace_row:
        return {"ok": False}

    path = str(workspace_row.get("path") or "")
    if not path:
        return {"ok": False}

    git_remote = resolve_git_remote_from_workspace(path)
    if not git_remote.get("ok"):
        return {"ok": False}

    repo = normalize_github_repository_slug(str(git_remote.get("repository") or ""))
    if not repo:
        return {"ok": False}

    row = find_target_by_repo(repo)
    if row:
        resolved = target_to_resolution(row, source="registry_local_workspace")
        resolved["branch"] = str(git_remote.get("branch") or resolved.get("branch") or "main")
        resolved["local_path"] = path
        resolved["workspace_id"] = str(workspace_row.get("workspace_id") or "")
        return resolved

    basename = repo.split("/")[-1]
    return {
        "ok": True,
        "source": "local_workspace",
        "target_id": "",
        "alias": str(workspace_row.get("name") or basename),
        "repo": repo,
        "branch": str(git_remote.get("branch") or "main"),
        "project_name": basename,
        "vercel_project": basename,
        "railway_project": "",
        "railway_service": "",
        "railway_environment": "",
        "root_directory": "",
        "default_provider": "",
        "workspace_id": str(workspace_row.get("workspace_id") or ""),
        "local_path": path,
    }


def _save_session_deploy_target(
    session_id: str,
    *,
    repo_hint: str = "",
    repo: str = "",
    flow: str = "railway_greenfield",
    status: str = "pending",
    user_text: str = "",
    inventory_status: str = "",
) -> dict[str, Any]:
    sid = (session_id or "default").strip() or "default"
    record = {
        "session_id": sid,
        "repo_hint": (repo_hint or "").strip(),
        "repo": normalize_github_repository_slug((repo or "").strip()),
        "flow": (flow or "railway_greenfield").strip(),
        "status": (status or "pending").strip(),
        "user_text": (user_text or "").strip(),
        "inventory_status": (inventory_status or "").strip(),
        "updated_at": time(),
        "expires_at": time() + _SESSION_TARGET_TTL_SECONDS,
    }
    _SESSION_TARGET_MEMORY[sid] = record
    index = _load_session_target_index()
    sessions = dict(index.get("sessions") or {})
    sessions[sid] = record
    index["sessions"] = sessions
    index["updated_at"] = time()
    _atomic_write_session_index(index)
    return record


def _load_session_target_index() -> dict[str, Any]:
    path = session_deploy_targets_path()
    if not path.is_file():
        return {"sessions": {}, "updated_at": None}
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {"sessions": {}, "updated_at": None}
    if not isinstance(raw, dict):
        return {"sessions": {}, "updated_at": None}
    if not isinstance(raw.get("sessions"), dict):
        raw["sessions"] = {}
    return raw


def _atomic_write_session_index(payload: dict[str, Any]) -> None:
    path = session_deploy_targets_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(".tmp")
    tmp.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    tmp.replace(path)


def _extract_bare_repo_name_from_text(text: str) -> str:
    raw = (text or "").strip()
    if not raw:
        return ""
    match = _BARE_DEPLOY_NAME_RX.search(raw)
    if not match:
        return ""
    candidate = match.group(1).strip().lower()
    if not candidate or candidate in _BARE_NAME_STOPWORDS:
        return ""
    end = match.end(1)
    if end < len(raw) and raw[end] == "/":
        return ""
    if "/" in candidate:
        return ""
    return candidate


def _text_names_new_deploy_target(text: str) -> bool:
    raw = (text or "").strip()
    if not raw:
        return False
    if _resolve_explicit_repo(raw):
        return True
    bare = _extract_bare_repo_name_from_text(raw)
    return bool(bare)


def _resolve_bare_repo_via_github_inventory(bare_name: str) -> dict[str, Any]:
    hint = (bare_name or "").strip()
    if not hint:
        return {"ok": False, "blocker_code": "DEPLOYMENT_TARGET_UNRESOLVED", "detail": "Empty repository name."}

    from aethos_core.credentials import get_provider_api_token
    from aethos_core.providers.github.api_client import list_repositories

    token = get_provider_api_token("github", require_validated=False)
    if not token:
        return {
            "ok": False,
            "blocker_code": "GITHUB_CREDENTIAL_MISSING",
            "detail": "Connect GitHub in Mission Control → Advanced settings → Credentials to resolve repository names.",
            "safe_next_command": "Add a GitHub API token in Mission Control → Advanced settings → Credentials, then retry.",
        }

    listed = list_repositories(token)
    if not listed.get("ok"):
        return {
            "ok": False,
            "blocker_code": "GITHUB_INVENTORY_FAILED",
            "detail": str(listed.get("error") or "GitHub repository list failed."),
            "safe_next_command": "Verify the GitHub token in Mission Control → Advanced settings → Credentials.",
        }

    repos = listed.get("repositories") or []
    names = [
        str(row.get("full_name") or "")
        for row in repos
        if isinstance(row, dict) and str(row.get("full_name") or "").strip()
    ]
    hint_lower = hint.lower()
    exact = [name for name in names if name.split("/")[-1].lower() == hint_lower]

    if len(exact) == 1:
        return {"ok": True, "repo": exact[0], "source": "github_inventory"}
    if len(exact) > 1:
        preview = ", ".join(f"`{name}`" for name in exact[:8])
        return {
            "ok": False,
            "blocker_code": "DEPLOYMENT_TARGET_AMBIGUOUS",
            "detail": f"Multiple connected repos named `{hint}`: {preview}.",
            "safe_next_command": "Reply with the full owner/repo you want to deploy.",
            "matches": exact,
        }

    preview = ", ".join(f"`{name}`" for name in names[:12])
    suffix = f" Connected repos: {preview}." if preview else ""
    return {
        "ok": False,
        "blocker_code": "DEPLOYMENT_TARGET_NOT_IN_INVENTORY",
        "detail": f"No connected repo named `{hint}`.{suffix}",
        "safe_next_command": (
            f"Connect the repo in GitHub or name the full owner/repo (e.g. pilotmain/{hint})."
        ),
        "matches": names[:20],
    }


def _inventory_resolution_failure(bare_name: str, inventory: dict[str, Any]) -> dict[str, Any]:
    code = str(inventory.get("blocker_code") or "DEPLOYMENT_TARGET_UNRESOLVED")
    detail = str(inventory.get("detail") or f"Could not resolve repository `{bare_name}`.")
    safe_next = str(
        inventory.get("safe_next_command")
        or f"Name the full owner/repo (e.g. pilotmain/{bare_name}) or connect GitHub."
    )
    return {
        "ok": False,
        "blocker_code": code,
        "detail": detail,
        "safe_next_command": safe_next,
        "matches": list(inventory.get("matches") or []),
    }

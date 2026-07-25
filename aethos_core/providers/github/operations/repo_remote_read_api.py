# SPDX-License-Identifier: Apache-2.0
"""Read-only GitHub repo snapshot via API — tree + bounded file contents (hosted-safe)."""

from __future__ import annotations

import base64
import json
import re
from typing import Any

from aethos_core.providers.github.api_client import parse_owner_repo, request_github
from aethos_core.providers.github.operations.repo_readonly_api import inspect_repo
from aethos_core.providers.github.shared.workflow_resolution import resolve_repository
from aethos_core.providers.railway.deployment_plan.repo_inspection import infer_deployment_fields_from_files

_MAX_TREE_ENTRIES = 2000
_MAX_FILES = 24
_MAX_FILE_BYTES = 12_000

_PRIORITY_ROOT_FILES = (
    "package.json",
    "pyproject.toml",
    "requirements.txt",
    "Pipfile",
    "go.mod",
    "Cargo.toml",
    "Dockerfile",
    "docker-compose.yml",
    "docker-compose.yaml",
    "Makefile",
    "railway.json",
    "nixpacks.toml",
    "Procfile",
    ".env.example",
    "README.md",
    "tsconfig.json",
    "next.config.js",
    "next.config.ts",
    "vite.config.ts",
    "turbo.json",
)

_SKIP_PATH_RX = re.compile(
    r"(?:^|/)(?:node_modules|\.git|dist|build|\.next|coverage|__pycache__|\.venv|vendor)(?:/|$)",
    re.I,
)
_ANALYSIS_VERBS_RX = re.compile(
    r"\b(?:look\s+into|review|analy(?:z|s)e|inspect|audit|walk\s+through|go\s+through|"
    r"suggest\s+(?:enhancement|improvement)s?|enhance|improve|explain)\b",
    re.I,
)
_OWNER_REPO_RX = re.compile(r"\b([a-z0-9][\w.-]+/[a-z0-9][\w.-]+)\b", re.I)
_GITHUB_MENTION_RX = re.compile(r"\b(?:on\s+)?github\b|github\.com/", re.I)
_REPO_ON_GITHUB_RX = re.compile(r"\b([a-z0-9][a-z0-9._-]+)\s+on\s+github\b", re.I)
_SKIP_REPO_WORDS = frozenset(
    {
        "github",
        "look",
        "into",
        "suggest",
        "enhancement",
        "enhancements",
        "improvement",
        "improvements",
        "review",
        "analyze",
        "analysis",
        "inspect",
        "audit",
        "repo",
        "repository",
        "code",
        "source",
        "the",
        "and",
        "for",
        "my",
        "your",
        "this",
        "that",
        "please",
        "connected",
        "access",
        "job",
    }
)


def _github_token() -> str | None:
    from aethos_core.credentials import get_provider_api_token

    token = get_provider_api_token("github")
    return str(token).strip() if token else None


def _decode_content(raw: str) -> str:
    cleaned = (raw or "").replace("\n", "").strip()
    if not cleaned:
        return ""
    try:
        return base64.b64decode(cleaned).decode("utf-8", errors="replace")
    except Exception:
        return ""


def _fetch_file_content(
    token: str,
    *,
    owner: str,
    repo: str,
    path: str,
    ref: str,
) -> str | None:
    result = request_github(
        token,
        "GET",
        f"/repos/{owner}/{repo}/contents/{path}",
        params={"ref": ref},
    )
    if not result.get("ok"):
        return None
    data = result.get("data")
    if isinstance(data, dict) and data.get("type") == "file":
        text = _decode_content(str(data.get("content") or ""))
        return text[:_MAX_FILE_BYTES] if text else ""
    return None


def _commit_tree_sha(token: str, *, owner: str, repo: str, commit_sha: str) -> str | None:
    result = request_github(token, "GET", f"/repos/{owner}/{repo}/git/commits/{commit_sha}")
    if not result.get("ok"):
        return None
    data = dict(result.get("data") or {})
    tree = data.get("tree")
    if isinstance(tree, dict):
        sha = str(tree.get("sha") or "").strip()
        return sha or None
    return None


def _fetch_recursive_tree(
    token: str,
    *,
    owner: str,
    repo: str,
    tree_sha: str,
) -> list[dict[str, Any]]:
    result = request_github(
        token,
        "GET",
        f"/repos/{owner}/{repo}/git/trees/{tree_sha}",
        params={"recursive": "1"},
    )
    if not result.get("ok"):
        return []
    data = dict(result.get("data") or {})
    raw = data.get("tree")
    if not isinstance(raw, list):
        return []
    entries: list[dict[str, Any]] = []
    for item in raw[:_MAX_TREE_ENTRIES]:
        if not isinstance(item, dict):
            continue
        path = str(item.get("path") or "").strip()
        if not path or _SKIP_PATH_RX.search(path):
            continue
        entries.append(
            {
                "path": path,
                "type": str(item.get("type") or ""),
                "size": item.get("size"),
            }
        )
    return entries


def _select_key_paths(tree_entries: list[dict[str, Any]]) -> list[str]:
    blobs = [e for e in tree_entries if e.get("type") == "blob"]
    paths = [str(e["path"]) for e in blobs if e.get("path")]
    selected: list[str] = []
    seen: set[str] = set()

    def add(path: str) -> None:
        if path and path not in seen:
            seen.add(path)
            selected.append(path)

    for name in _PRIORITY_ROOT_FILES:
        if name in paths:
            add(name)

    for path in paths:
        if path.startswith(".github/workflows/") and path.endswith((".yml", ".yaml")):
            add(path)

    for path in paths:
        lower = path.lower()
        if lower.startswith("src/") and lower.endswith((".py", ".ts", ".tsx", ".js", ".jsx", ".go", ".rs")):
            add(path)
            if len(selected) >= _MAX_FILES:
                break

    for path in paths:
        if path.count("/") <= 1 and path.endswith((".py", ".ts", ".tsx", ".js", ".jsx", ".go")):
            add(path)
            if len(selected) >= _MAX_FILES:
                break

    return selected[:_MAX_FILES]


def _directory_map(tree_entries: list[dict[str, Any]], *, max_dirs: int = 40) -> list[str]:
    dirs: list[str] = []
    for entry in tree_entries:
        if entry.get("type") != "tree":
            continue
        path = str(entry.get("path") or "").strip()
        if not path:
            continue
        depth = path.count("/")
        if depth <= 2:
            dirs.append(path)
        if len(dirs) >= max_dirs:
            break
    return sorted(dirs)


def _detect_stack(file_contents: dict[str, str], deployment_fields: dict[str, Any]) -> list[str]:
    badges: list[str] = []
    if deployment_fields.get("runtime"):
        badges.append(str(deployment_fields["runtime"]))
    if deployment_fields.get("framework"):
        badges.append(str(deployment_fields["framework"]))
    if "package.json" in file_contents:
        badges.append("Node.js")
    if "pyproject.toml" in file_contents or "requirements.txt" in file_contents:
        badges.append("Python")
    if "go.mod" in file_contents:
        badges.append("Go")
    if "Cargo.toml" in file_contents:
        badges.append("Rust")
    if "Dockerfile" in file_contents:
        badges.append("Docker")
    return list(dict.fromkeys(badges))


def is_github_remote_repo_analysis_request(text: str) -> bool:
    """True when the user wants analysis of a remote GitHub repo (not a local path)."""
    raw = (text or "").strip()
    if not raw:
        return False

    if _OWNER_REPO_RX.search(raw) and _ANALYSIS_VERBS_RX.search(raw):
        return True

    from aethos_core.local_workspace.portfolio import extract_filesystem_paths

    if extract_filesystem_paths(raw):
        return False
    from aethos_core.remote_workspace.github_clone import parse_github_repository

    if parse_github_repository(raw) and _ANALYSIS_VERBS_RX.search(raw):
        return True
    if _GITHUB_MENTION_RX.search(raw) and _ANALYSIS_VERBS_RX.search(raw):
        return extract_github_repo_hint(raw) is not None
    if _REPO_ON_GITHUB_RX.search(raw):
        return True
    return False


def extract_github_repo_hint(text: str) -> str | None:
    """Extract owner/repo or repo name hint from natural language."""
    raw = (text or "").strip()
    if not raw:
        return None
    from aethos_core.remote_workspace.github_clone import parse_github_repository

    parsed = parse_github_repository(raw)
    if parsed:
        return parsed
    owner_repo = _OWNER_REPO_RX.search(raw)
    if owner_repo:
        return owner_repo.group(1).strip()
    m = _REPO_ON_GITHUB_RX.search(raw)
    if m:
        return m.group(1).strip()
    if _GITHUB_MENTION_RX.search(raw):
        for match in re.finditer(r"\b([a-z][a-z0-9._-]{2,})\b", raw, re.I):
            word = match.group(1)
            if word.lower() in _SKIP_REPO_WORDS:
                continue
            return word
    return None


def build_github_repo_snapshot(
    repository: str,
    *,
    branch: str | None = None,
) -> dict[str, Any]:
    """Fetch bounded tree + key file contents for owner/repo via GitHub API."""
    token = _github_token()
    if not token:
        return {
            "ok": False,
            "error": "github_token_unavailable",
            "hint": "Connect GitHub in Mission Control → Advanced settings → Credentials first.",
            "repository": repository,
        }

    resolved = resolve_repository(token, repository=(repository or "").strip())
    if not resolved.get("ok"):
        return {
            "ok": False,
            "error": str(resolved.get("error") or "repository_not_resolved"),
            "repository": repository,
        }

    owner = str(resolved["owner"])
    repo = str(resolved["repo"])
    full_name = str(resolved["full_name"])

    meta = inspect_repo(token, repository=full_name)
    if not meta.get("ok"):
        return {
            "ok": False,
            "error": str(meta.get("error") or "repo_metadata_unavailable"),
            "repository": full_name,
        }

    ref = (branch or "").strip() or str(meta.get("default_branch") or "main")
    branch_result = request_github(token, "GET", f"/repos/{owner}/{repo}/branches/{ref}")
    if not branch_result.get("ok"):
        return {
            "ok": False,
            "error": str(branch_result.get("error") or "branch_unavailable"),
            "repository": full_name,
            "branch": ref,
        }
    branch_data = dict(branch_result.get("data") or {})
    commit = dict(branch_data.get("commit") or {})
    commit_sha = str(commit.get("sha") or "").strip()
    if not commit_sha:
        return {"ok": False, "error": "commit_sha_missing", "repository": full_name, "branch": ref}

    tree_sha = _commit_tree_sha(token, owner=owner, repo=repo, commit_sha=commit_sha)
    if not tree_sha:
        return {"ok": False, "error": "tree_sha_missing", "repository": full_name, "branch": ref}

    tree_entries = _fetch_recursive_tree(token, owner=owner, repo=repo, tree_sha=tree_sha)
    key_paths = _select_key_paths(tree_entries)
    file_contents: dict[str, str] = {}
    for path in key_paths:
        text = _fetch_file_content(token, owner=owner, repo=repo, path=path, ref=ref)
        if text is not None:
            file_contents[path] = text

    root_files = [p for p in key_paths if "/" not in p]
    deployment_fields = infer_deployment_fields_from_files(root_files=root_files, file_contents=file_contents)
    stack = _detect_stack(file_contents, deployment_fields)
    workflows = sorted(p for p in file_contents if p.startswith(".github/workflows/"))

    return {
        "ok": True,
        "repository": full_name,
        "branch": ref,
        "commit_sha": commit_sha[:12],
        "description": str(meta.get("description") or ""),
        "pushed_at": str(meta.get("pushed_at") or ""),
        "html_url": str(meta.get("html_url") or ""),
        "stack": stack,
        "deployment_fields": deployment_fields,
        "directory_map": _directory_map(tree_entries),
        "tree_file_count": len([e for e in tree_entries if e.get("type") == "blob"]),
        "files_read": sorted(file_contents.keys()),
        "file_contents": file_contents,
        "workflows": workflows,
        "manifests": [p for p in file_contents if p in _PRIORITY_ROOT_FILES],
    }


def _enhancement_observations(snapshot: dict[str, Any]) -> list[str]:
    observations: list[str] = []
    files_read = set(snapshot.get("files_read") or [])
    tree_count = int(snapshot.get("tree_file_count") or 0)
    workflows = list(snapshot.get("workflows") or [])

    if not workflows:
        observations.append(
            "No GitHub Actions workflows detected — add CI for lint, test, and deploy gates."
        )
    if "README.md" not in files_read:
        observations.append("README is missing or empty — document setup, architecture, and run commands.")
    if "tests" not in (snapshot.get("directory_map") or []) and not any(
        "test" in p.lower() for p in files_read
    ):
        observations.append("No obvious test directory — add unit/integration coverage for critical paths.")
    if ".env.example" not in files_read and "Dockerfile" in files_read:
        observations.append("Add `.env.example` listing required environment variables for deploy parity.")
    if tree_count > 400 and not workflows:
        observations.append(
            f"Large codebase ({tree_count} tracked files) without CI — prioritize automated quality gates."
        )

    pkg = (snapshot.get("file_contents") or {}).get("package.json")
    if pkg:
        try:
            data = json.loads(pkg)
            deps = data.get("dependencies") or {}
            if isinstance(deps, dict) and len(deps) > 40:
                observations.append(
                    f"package.json lists {len(deps)} runtime dependencies — audit for unused or duplicate packages."
                )
            scripts = data.get("scripts") or {}
            if isinstance(scripts, dict) and not any(
                k in scripts for k in ("test", "lint", "typecheck", "check")
            ):
                observations.append("package.json has no test/lint script — wire `npm test` / `npm run lint`.")
        except json.JSONDecodeError:
            observations.append("package.json is not valid JSON — fix manifest parsing failures.")

    pyproject = (snapshot.get("file_contents") or {}).get("pyproject.toml")
    if pyproject and "[tool.ruff" not in pyproject and "[tool.black" not in pyproject:
        observations.append("Python project without Ruff/Black config — standardize lint/format in CI.")

    return observations


def format_github_enhancement_report(snapshot: dict[str, Any]) -> str:
    """Markdown enhancement analysis from a repo snapshot."""
    if not snapshot.get("ok"):
        error = str(snapshot.get("error") or "snapshot_failed")
        hint = str(snapshot.get("hint") or "").strip()
        lines = [
            "# GitHub repo analysis unavailable",
            "",
            f"**Error:** {error}",
        ]
        if hint:
            lines.append(f"**Next step:** {hint}")
        return "\n".join(lines)

    repo = str(snapshot.get("repository") or "")
    stack = snapshot.get("stack") or []
    dirs = snapshot.get("directory_map") or []
    files_read = snapshot.get("files_read") or []
    workflows = snapshot.get("workflows") or []
    observations = _enhancement_observations(snapshot)

    lines = [
        f"# GitHub repo analysis — `{repo}`",
        "",
        f"**Branch:** {snapshot.get('branch') or 'main'} · "
        f"**Last push:** {snapshot.get('pushed_at') or '—'} · "
        f"**Files sampled:** {len(files_read)} (API read-only)",
        "",
        "## Stack & manifests",
        "",
    ]
    if stack:
        lines.append(f"- **Detected:** {', '.join(stack)}")
    else:
        lines.append("- **Detected:** (no dominant stack from sampled manifests)")
    for manifest in snapshot.get("manifests") or []:
        lines.append(f"- `{manifest}`")

    lines.extend(["", "## Structure", "", f"- **Tracked files (sampled tree):** {snapshot.get('tree_file_count', 0)}"])
    if dirs:
        lines.append("- **Top directories:** " + ", ".join(f"`{d}`" for d in dirs[:12]))

    lines.extend(["", "## CI / workflows", ""])
    if workflows:
        for wf in workflows:
            lines.append(f"- `{wf}`")
    else:
        lines.append("- None detected in sampled tree.")

    lines.extend(["", "## Enhancement opportunities", ""])
    if observations:
        for item in observations:
            lines.append(f"- {item}")
    else:
        lines.append("- Sampled tree looks well-structured — drill into hot paths for deeper refactors.")

    excerpts = snapshot.get("file_contents") or {}
    if excerpts.get("README.md"):
        readme = excerpts["README.md"].strip()
        preview = readme[:600] + ("…" if len(readme) > 600 else "")
        lines.extend(["", "## README excerpt", "", preview])

    lines.extend(
        [
            "",
            "_Read via GitHub API (no local workspace registration required on hosted)._",
        ]
    )
    return "\n".join(lines)


def analyze_github_repo_for_chat(
    text: str,
    *,
    repository: str | None = None,
    branch: str | None = None,
) -> dict[str, Any]:
    """Build snapshot + formatted report for chat/engineering lanes."""
    hint = (repository or "").strip() or extract_github_repo_hint(text) or ""
    snapshot = build_github_repo_snapshot(hint, branch=branch)
    report = format_github_enhancement_report(snapshot)
    return {"ok": bool(snapshot.get("ok")), "snapshot": snapshot, "report": report, "repository": snapshot.get("repository")}

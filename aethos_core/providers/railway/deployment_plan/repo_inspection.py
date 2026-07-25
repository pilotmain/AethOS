# SPDX-License-Identifier: Apache-2.0
"""Readonly GitHub repo inspection for Railway deployment plan completion."""

from __future__ import annotations

import base64
import json
import re
from typing import Any

from aethos_core.providers.github.api_client import parse_owner_repo, request_github

_MANIFEST_PATHS = (
    "package.json",
    "pyproject.toml",
    "requirements.txt",
    "Dockerfile",
    "Procfile",
    "railway.json",
    "nixpacks.toml",
    ".env.example",
    "README.md",
)

_ENV_KEY_RX = re.compile(r"^([A-Z][A-Z0-9_]{1,127})\s*=", re.M)
_README_HEALTH_RX = re.compile(r"(/[\w-]*health[\w-]*)", re.I)
_README_START_RX = re.compile(
    r"(?:^|[\n`])"
    r"((?:uvicorn|gunicorn|python\s+-m|npm\s+(?:run\s+)?start|yarn\s+start|node\s+)[^\n`]{4,200})",
    re.I | re.M,
)
_HEALTH_PROBE_RX = re.compile(
    r"(?i)"
    r"(?:^|\s)(?:curl|wget)\s+[^\n|&;]*(?:/health|healthz|healthcheck)"
    r"|^\s*HEALTHCHECK\b"
    r"|\|\|\s*exit\s+1\s*$"
)


def _decode_content(raw: str) -> str:
    cleaned = (raw or "").replace("\n", "").strip()
    if not cleaned:
        return ""
    try:
        return base64.b64decode(cleaned).decode("utf-8", errors="replace")
    except Exception:
        return ""


def _fetch_repo_file(
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
    if isinstance(data, dict):
        if data.get("type") == "file":
            return _decode_content(str(data.get("content") or ""))[:24000]
        return None
    return None


def _list_root_files(token: str, *, owner: str, repo: str, ref: str) -> list[str]:
    result = request_github(
        token,
        "GET",
        f"/repos/{owner}/{repo}/contents/",
        params={"ref": ref},
    )
    if not result.get("ok"):
        return []
    data = result.get("data")
    if not isinstance(data, list):
        return []
    names: list[str] = []
    for entry in data:
        if isinstance(entry, dict) and entry.get("type") == "file":
            name = str(entry.get("name") or "").strip()
            if name:
                names.append(name)
    return names


def inspect_github_repo_for_deployment(
    *,
    repository: str,
    branch: str = "main",
) -> dict[str, Any]:
    """Readonly repo inspection — no secrets, no mutation."""
    repo = (repository or "").strip()
    ref = (branch or "main").strip() or "main"
    owner, name = parse_owner_repo(repo)
    if not owner or not name:
        return {
            "ok": False,
            "repository": repo,
            "branch": ref,
            "error": f"Could not parse repository `{repo}`.",
        }

    from aethos_core.credentials import get_provider_api_token

    token = get_provider_api_token("github")
    if not token:
        return {
            "ok": False,
            "repository": f"{owner}/{name}",
            "branch": ref,
            "error": "GitHub credential unavailable for readonly repo inspection.",
        }

    root_files = _list_root_files(token, owner=owner, repo=name, ref=ref)
    file_contents: dict[str, str] = {}
    for path in _MANIFEST_PATHS:
        if path in root_files:
            text = _fetch_repo_file(token, owner=owner, repo=name, path=path, ref=ref)
            if text is not None:
                file_contents[path] = text

    fields = infer_deployment_fields_from_files(root_files=root_files, file_contents=file_contents)
    return {
        "ok": True,
        "repository": f"{owner}/{name}",
        "branch": ref,
        "root_files": root_files,
        "files_inspected": sorted(file_contents.keys()),
        "fields": fields,
    }


def is_health_probe_command(command: str) -> bool:
    """True when a command is a health/verification probe, not an app entrypoint."""
    raw = (command or "").strip()
    if not raw:
        return False
    if _HEALTH_PROBE_RX.search(raw):
        return True
    lower = raw.lower()
    if ("127.0.0.1" in lower or "localhost" in lower) and "health" in lower:
        return True
    if lower.startswith("curl ") and "health" in lower:
        return True
    return False


def _sanitize_start_command(command: str | None) -> str:
    cmd = (command or "").strip()
    if not cmd or is_health_probe_command(cmd):
        return "unknown"
    return cmd


def extract_env_var_names_from_text(text: str) -> list[str]:
    names: list[str] = []
    seen: set[str] = set()
    for match in _ENV_KEY_RX.finditer(text or ""):
        key = match.group(1).strip()
        if key and key not in seen and key not in {"EXPORT", "ENV"}:
            seen.add(key)
            names.append(key)
    return names


def extract_env_var_hints_from_text(text: str) -> dict[str, str]:
    """Map env var names to inline `# comment` purpose hints from `.env.example`."""
    hints: dict[str, str] = {}
    for line in (text or "").splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        if "=" not in stripped:
            continue
        name_part, _, rest = stripped.partition("=")
        name = name_part.strip().upper()
        if not name:
            continue
        comment = ""
        if "#" in rest:
            _, _, comment = rest.partition("#")
        if comment.strip():
            hints[name] = comment.strip()[:160]
    return hints


def infer_deployment_fields_from_files(
    *,
    root_files: list[str],
    file_contents: dict[str, str],
) -> dict[str, Any]:
    """Pure inference from manifest contents (testable without GitHub API)."""
    root_set = {name.lower() for name in root_files}
    has = lambda name: name.lower() in root_set or name in file_contents

    railway_cfg: dict[str, Any] = {}
    if "railway.json" in file_contents:
        try:
            railway_cfg = json.loads(file_contents["railway.json"])
        except json.JSONDecodeError:
            railway_cfg = {}

    package: dict[str, Any] = {}
    if "package.json" in file_contents:
        try:
            package = json.loads(file_contents["package.json"])
        except json.JSONDecodeError:
            package = {}

    runtime = "unknown"
    build_command = "unknown"
    start_command = "unknown"
    health_check_path: str | None = None
    notes: list[str] = []

    railway_build = ((railway_cfg.get("build") or {}) if isinstance(railway_cfg.get("build"), dict) else {})
    railway_deploy = ((railway_cfg.get("deploy") or {}) if isinstance(railway_cfg.get("deploy"), dict) else {})
    if railway_cfg:
        rb = str(railway_build.get("buildCommand") or railway_build.get("command") or "").strip()
        rs = str(railway_deploy.get("startCommand") or railway_deploy.get("command") or "").strip()
        if rb:
            build_command = rb
            notes.append("build from railway.json")
        if rs and not is_health_probe_command(rs):
            start_command = rs
            notes.append("start from railway.json")
        elif rs and is_health_probe_command(rs):
            notes.append("ignored railway.json start (health probe)")
        hc = str(railway_deploy.get("healthcheckPath") or railway_cfg.get("healthcheckPath") or "").strip()
        if hc:
            health_check_path = hc

    procfile = file_contents.get("Procfile", "")
    if procfile:
        web_cmd = _procfile_web_command(procfile)
        if web_cmd and start_command == "unknown":
            start_command = _sanitize_start_command(web_cmd)
            if start_command != "unknown":
                notes.append("start from Procfile web")
                if runtime == "unknown":
                    runtime = "Python" if re.search(r"uvicorn|gunicorn", web_cmd, re.I) else runtime

    dockerfile = file_contents.get("Dockerfile", "")
    if has("Dockerfile") and dockerfile:
        docker_start, docker_health = _dockerfile_start_and_health(dockerfile)
        if docker_health and not health_check_path:
            health_check_path = docker_health
            notes.append("health from Dockerfile HEALTHCHECK")
        if docker_start and start_command == "unknown":
            start_command = docker_start
            notes.append("start from Dockerfile CMD/ENTRYPOINT")
        if runtime == "unknown":
            runtime = "Docker"
            if build_command == "unknown":
                build_command = "docker build ."

    if has("package.json") and package:
        runtime = "Node"
        scripts = package.get("scripts") if isinstance(package.get("scripts"), dict) else {}
        if build_command == "unknown":
            if scripts.get("build"):
                build_command = "npm ci && npm run build"
            else:
                build_command = "npm ci"
        if start_command == "unknown":
            if scripts.get("start"):
                start_command = "npm start"
            elif package.get("main"):
                start_command = f"node {package['main']}"
            else:
                start_command = "npm start"

    py_start = _infer_python_start(file_contents)
    if has("pyproject.toml") or has("requirements.txt") or has("setup.py"):
        if runtime == "unknown" or runtime == "Docker" and py_start:
            runtime = "Python"
        if build_command == "unknown" or build_command == "docker build .":
            if has("requirements.txt"):
                build_command = "pip install -r requirements.txt"
            elif has("pyproject.toml"):
                build_command = "pip install ."
        if start_command == "unknown" and py_start:
            start_command = _sanitize_start_command(py_start)
            if start_command != "unknown":
                notes.append("start from Python manifests")

    if "README.md" in file_contents:
        readme = file_contents["README.md"]
        if start_command == "unknown":
            readme_start = _readme_start_command(readme)
            if readme_start:
                start_command = readme_start
                notes.append("start from README example")
        if not health_check_path:
            hm = _README_HEALTH_RX.search(readme)
            if hm:
                health_check_path = hm.group(1)

    env_names: list[str] = []
    if ".env.example" in file_contents:
        env_names.extend(extract_env_var_names_from_text(file_contents[".env.example"]))
    env_names = sorted({name for name in env_names if name})

    start_command = _sanitize_start_command(start_command)

    pkg_name = str(package.get("name") or "").strip()
    service_name_confidence = "low"
    if str(railway_cfg.get("name") or "").strip():
        service_name_confidence = "high"
    elif pkg_name:
        service_name_confidence = "medium"

    if runtime == "unknown":
        if has("Dockerfile"):
            runtime = "Docker"
        elif has("package.json"):
            runtime = "Node"
        elif has("pyproject.toml") or has("requirements.txt"):
            runtime = "Python"

    return {
        "runtime": runtime,
        "build_command": build_command,
        "start_command": start_command,
        "health_check_path": health_check_path or "unknown",
        "required_env_var_names": env_names,
        "service_name_confidence": service_name_confidence,
        "package_name": pkg_name,
        "inspection_notes": notes,
        "manifests_present": sorted(file_contents.keys()),
    }


def _dockerfile_start_and_health(dockerfile: str) -> tuple[str | None, str | None]:
    start: str | None = None
    health_path: str | None = None
    entrypoint_parts: list[str] = []

    for line in dockerfile.splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        health_match = re.match(r"^HEALTHCHECK\s+(.+)$", stripped, re.I)
        if health_match:
            probe = health_match.group(1).strip()
            path_match = re.search(r"https?://[^/\s'\"]+(/[^\s'\"`)]+)", probe, re.I)
            if path_match:
                health_path = path_match.group(1)
            continue
        entry_match = re.match(r"^ENTRYPOINT\s+(.+)$", stripped, re.I)
        if entry_match:
            entrypoint_parts = [_strip_json_exec(entry_match.group(1))]
            continue
        cmd_match = re.match(r"^CMD\s+(.+)$", stripped, re.I)
        if cmd_match:
            cmd = _strip_json_exec(cmd_match.group(1))
            combined = " ".join(part for part in [*entrypoint_parts, cmd] if part).strip()
            if combined and not is_health_probe_command(combined):
                start = combined
    return (start, health_path)


def _strip_json_exec(fragment: str) -> str:
    raw = (fragment or "").strip()
    if raw.startswith("["):
        try:
            parsed = json.loads(raw)
            if isinstance(parsed, list):
                return " ".join(str(part) for part in parsed)
        except json.JSONDecodeError:
            pass
    return raw.strip("\"' ")


def _readme_start_command(readme: str) -> str | None:
    for match in _README_START_RX.finditer(readme or ""):
        candidate = match.group(1).strip()
        if candidate and not is_health_probe_command(candidate):
            return candidate
    return None


def _procfile_web_command(procfile: str) -> str | None:
    for line in procfile.splitlines():
        stripped = line.strip()
        if stripped.lower().startswith("web:"):
            return stripped.split(":", 1)[1].strip()
    return None


def _infer_python_start(file_contents: dict[str, str]) -> str | None:
    proc = _procfile_web_command(file_contents.get("Procfile", ""))
    if proc and not is_health_probe_command(proc):
        return proc
    pyproject = file_contents.get("pyproject.toml", "")
    scripts_match = re.search(r"\[project\.scripts\][^\[]*?(\w+)\s*=\s*['\"]([^'\"]+)['\"]", pyproject, re.S)
    if scripts_match:
        return scripts_match.group(2)
    req = file_contents.get("requirements.txt", "").lower()
    if "fastapi" in req or "uvicorn" in req:
        return "uvicorn main:app --host 0.0.0.0 --port $PORT"
    if "flask" in req:
        return "gunicorn app:app --bind 0.0.0.0:$PORT"
    if "django" in req:
        return "gunicorn config.wsgi:application --bind 0.0.0.0:$PORT"
    return None

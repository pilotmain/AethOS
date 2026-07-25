# SPDX-License-Identifier: Apache-2.0
"""Workspace stack and tooling detection."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def scan_workspace_stack(repo: Path) -> dict[str, Any]:
    badges: list[str] = []
    package_managers: list[str] = []
    languages: list[str] = []

    if (repo / "package.json").is_file() or (repo / "web" / "package.json").is_file():
        badges.append("node")
        package_managers.append("npm")
        languages.append("typescript/javascript")
    if (repo / "pyproject.toml").is_file() or (repo / "requirements.txt").is_file():
        badges.append("python")
        package_managers.append("pip/poetry")
        languages.append("python")
    if (repo / "pom.xml").is_file():
        badges.append("java")
        package_managers.append("maven")
        languages.append("java")
    if (repo / "build.gradle").is_file() or (repo / "build.gradle.kts").is_file():
        badges.append("java")
        package_managers.append("gradle")
        languages.append("java/kotlin")
    if (repo / "docker-compose.yml").is_file() or (repo / "docker-compose.yaml").is_file():
        badges.append("docker-compose")
    if (repo / "Dockerfile").is_file():
        badges.append("docker")
    if (repo / ".github" / "workflows").is_dir():
        badges.append("github-actions")
    if (repo / "kubernetes").is_dir() or (repo / "k8s").is_dir():
        badges.append("kubernetes")

    return {
        "badges": sorted(set(badges)),
        "package_managers": sorted(set(package_managers)),
        "languages": sorted(set(languages)),
        "has_git": (repo / ".git").is_dir(),
    }


def read_package_scripts(repo: Path) -> dict[str, Any]:
    for candidate in (repo / "web" / "package.json", repo / "package.json"):
        if candidate.is_file():
            try:
                data = json.loads(candidate.read_text(encoding="utf-8"))
                scripts = dict(data.get("scripts") or {})
                return {"path": str(candidate), "scripts": scripts}
            except (OSError, json.JSONDecodeError):
                continue
    return {"path": None, "scripts": {}}

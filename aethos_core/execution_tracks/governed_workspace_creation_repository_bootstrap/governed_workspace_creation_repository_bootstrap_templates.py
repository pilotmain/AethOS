# SPDX-License-Identifier: Apache-2.0
"""FIX 334 — approved project template definitions for repository bootstrap."""

from __future__ import annotations

import json
from typing import Any

from aethos_core.execution_tracks.governed_workspace_creation_repository_bootstrap.governed_workspace_creation_repository_bootstrap_contract import (
    SUPPORTED_REPOSITORY_TEMPLATES,
)


def _governance_metadata(*, workspace_name: str, template_id: str, session_id: str) -> str:
    payload = {
        "schema_version": "aethos_governance_metadata_v1",
        "workspace_name": workspace_name,
        "template_id": template_id,
        "session_id": session_id,
        "execution_track": "EXECUTION_TRACK_1",
        "deployment_authority": False,
        "trust_mutation": False,
        "bootstrap_only": True,
    }
    return json.dumps(payload, indent=2, sort_keys=True)


def _readme(*, workspace_name: str, template_id: str) -> str:
    return (
        f"# {workspace_name}\n\n"
        f"Governed workspace bootstrapped from template `{template_id}`.\n\n"
        "This repository skeleton was prepared by AethOS EXECUTION_TRACK_1 under human review.\n"
        "Repository preparation only — no deployment authority.\n"
    )


def get_project_template(template_id: str) -> dict[str, Any] | None:
    normalized = str(template_id or "").strip().lower()
    if normalized not in SUPPORTED_REPOSITORY_TEMPLATES:
        return None
    return dict(_TEMPLATES[normalized])


def list_project_templates() -> list[dict[str, Any]]:
    return [
        {
            "template_id": template_id,
            "display_name": _TEMPLATES[template_id]["display_name"],
            "stack": _TEMPLATES[template_id]["stack"],
            "readiness": _TEMPLATES[template_id]["readiness"],
            "folder_count": len(_TEMPLATES[template_id]["folders"]),
            "file_count": len(_TEMPLATES[template_id]["files"]),
        }
        for template_id in SUPPORTED_REPOSITORY_TEMPLATES
    ]


def render_template_files(*, workspace_name: str, template_id: str, session_id: str) -> dict[str, str]:
    template = get_project_template(template_id)
    if template is None:
        return {}
    files = dict(template.get("files") or {})
    files["README.md"] = _readme(workspace_name=workspace_name, template_id=template_id)
    files["aethos/governance-metadata.json"] = _governance_metadata(
        workspace_name=workspace_name,
        template_id=template_id,
        session_id=session_id,
    )
    return files


_TEMPLATES: dict[str, dict[str, Any]] = {
    "spring_boot_service": {
        "display_name": "Spring Boot Service",
        "stack": "Java / Spring Boot",
        "readiness": "READY",
        "folders": [
            "src/main/java",
            "src/main/resources",
            "src/test/java",
            ".github/workflows",
            "aethos",
        ],
        "files": {
            "pom.xml": (
                '<?xml version="1.0" encoding="UTF-8"?>\n'
                "<project>\n"
                "  <modelVersion>4.0.0</modelVersion>\n"
                "  <groupId>com.example</groupId>\n"
                "  <artifactId>service</artifactId>\n"
                "  <version>0.0.1-SNAPSHOT</version>\n"
                "</project>\n"
            ),
            "src/main/resources/application.properties": "spring.application.name=service\n",
        },
    },
    "nextjs_web_app": {
        "display_name": "Next.js Web App",
        "stack": "TypeScript / Next.js",
        "readiness": "READY",
        "folders": ["app", "public", "components", ".github/workflows", "aethos"],
        "files": {
            "package.json": json.dumps(
                {"name": "nextjs-web-app", "private": True, "scripts": {"dev": "next dev"}},
                indent=2,
            )
            + "\n",
            "next.config.js": "/** @type {import('next').NextConfig} */\nmodule.exports = {};\n",
        },
    },
    "fastapi_service": {
        "display_name": "FastAPI Service",
        "stack": "Python / FastAPI",
        "readiness": "READY",
        "folders": ["app", "tests", ".github/workflows", "aethos"],
        "files": {
            "pyproject.toml": '[project]\nname = "fastapi-service"\nversion = "0.1.0"\n',
            "app/__init__.py": "",
        },
    },
    "fullstack_reference": {
        "display_name": "Fullstack Reference",
        "stack": "Next.js + FastAPI",
        "readiness": "READY",
        "folders": ["web", "api", "docs", ".github/workflows", "aethos"],
        "files": {
            "web/package.json": json.dumps({"name": "web", "private": True}, indent=2) + "\n",
            "api/pyproject.toml": '[project]\nname = "api"\nversion = "0.1.0"\n',
        },
    },
    "generic_repository": {
        "display_name": "Generic Repository",
        "stack": "Language-agnostic",
        "readiness": "READY",
        "folders": ["src", "tests", "docs", ".github/workflows", "aethos"],
        "files": {
            ".gitignore": "*.pyc\nnode_modules/\n.env\n",
        },
    },
}

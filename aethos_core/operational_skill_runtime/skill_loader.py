# SPDX-License-Identifier: Apache-2.0
"""Load provider SKILL.md files and bind to code skills."""

from __future__ import annotations

from pathlib import Path
from typing import Any

_SKILL_CACHE: dict[str, dict[str, Any]] = {}


def provider_skills_root() -> Path:
    from aethos_core.aethos_identity.identity_contract_loader import repo_root

    return repo_root() / "provider_skills"


def load_skill_markdown(provider: str) -> dict[str, Any]:
    provider = (provider or "").strip().lower()
    if provider in _SKILL_CACHE:
        return dict(_SKILL_CACHE[provider])

    path = provider_skills_root() / provider / "SKILL.md"
    if not path.is_file():
        payload = {"provider": provider, "loaded": False, "path": str(path), "content": ""}
        _SKILL_CACHE[provider] = payload
        return dict(payload)

    content = path.read_text(encoding="utf-8")
    payload = {
        "provider": provider,
        "loaded": True,
        "path": str(path),
        "content": content,
        "operations": _extract_bullet_section(content, "Supported operations"),
        "readonly_tools": _extract_bullet_section(content, "Readonly tools"),
        "mutation_tools": _extract_bullet_section(content, "Mutation tools"),
    }
    _SKILL_CACHE[provider] = payload
    return dict(payload)


def load_all_provider_skills(*, force: bool = False) -> dict[str, Any]:
    if force:
        _SKILL_CACHE.clear()

    from aethos_core.operational_skill_runtime.skill_registry import list_registered_providers, get_provider_skill

    loaded: list[dict[str, Any]] = []
    for provider in list_registered_providers():
        markdown = load_skill_markdown(provider)
        skill = get_provider_skill(provider)
        code_contract = skill.skill_contract() if skill is not None and hasattr(skill, "skill_contract") else {}
        loaded.append(
            {
                "provider": provider,
                "markdown_loaded": markdown.get("loaded"),
                "code_loaded": skill is not None,
                "supported_operations": code_contract.get("supported_operations") or markdown.get("operations") or [],
            }
        )
    return {
        "loaded_count": sum(1 for row in loaded if row["code_loaded"]),
        "markdown_count": sum(1 for row in loaded if row["markdown_loaded"]),
        "providers": loaded,
    }


def _extract_bullet_section(content: str, heading: str) -> list[str]:
    lines = content.splitlines()
    capture = False
    out: list[str] = []
    for line in lines:
        if line.strip().lower().startswith(f"## {heading.lower()}"):
            capture = True
            continue
        if capture and line.startswith("## "):
            break
        if capture and line.strip().startswith("- "):
            out.append(line.strip()[2:].strip())
    return out


_LOCAL_SKILL_CACHE: dict[str, Any] | None = None


def operator_skills_root() -> Path:
    from aethos_core.aethos_identity.identity_contract_loader import repo_root

    return repo_root() / "skills"


def load_local_operator_skills(*, force: bool = False) -> dict[str, Any]:
    global _LOCAL_SKILL_CACHE
    if _LOCAL_SKILL_CACHE is not None and not force:
        return dict(_LOCAL_SKILL_CACHE)

    root = operator_skills_root()
    loaded: list[dict[str, Any]] = []
    if root.is_dir():
        for path in sorted(root.glob("**/SKILL.md")):
            rel = path.relative_to(root)
            skill_id = str(rel.parent).replace("\\", "/")
            content = path.read_text(encoding="utf-8")
            loaded.append(
                {
                    "id": skill_id or "root",
                    "path": str(path),
                    "name": _read_operator_skill_frontmatter(content, "name") or skill_id,
                    "description": _read_operator_skill_frontmatter(content, "description") or "",
                    "loaded": True,
                }
            )
    payload = {"ok": True, "root": str(root), "count": len(loaded), "skills": loaded}
    _LOCAL_SKILL_CACHE = payload
    return dict(payload)


def reset_local_operator_skills_cache_for_tests() -> None:
    global _LOCAL_SKILL_CACHE
    _LOCAL_SKILL_CACHE = None


def _read_operator_skill_frontmatter(content: str, key: str) -> str:
    """Read a YAML-frontmatter ``key`` from a SKILL.md.

    Tolerant of leading content (e.g. an SPDX header) before the first ``---``
    fence, so a skill file is parsed even when it isn't the very first line.
    """
    lines = content.splitlines()
    start = None
    for idx, line in enumerate(lines):
        if line.strip() == "---":
            start = idx
            break
    if start is None:
        return ""
    for line in lines[start + 1 :]:
        if line.strip() == "---":
            break
        if line.strip().startswith(f"{key}:"):
            return line.split(":", 1)[1].strip().strip('"').strip("'")
    return ""


def local_operator_skills_snapshot() -> dict[str, Any]:
    return load_local_operator_skills()


def get_local_operator_skill(skill_id: str) -> dict[str, Any] | None:
    needle = (skill_id or "").strip().replace("\\", "/")
    if not needle:
        return None
    catalog = load_local_operator_skills()
    for row in catalog.get("skills") or []:
        if str(row.get("id") or "") == needle:
            path = str(row.get("path") or "")
            content = ""
            if path:
                try:
                    content = Path(path).read_text(encoding="utf-8")
                except OSError:
                    content = ""
            return {
                **row,
                "content": content,
            }
    return None


def mcp_tool_catalog() -> dict[str, Any]:
    from aethos_core.config import get_settings

    return {
        "ok": True,
        "enabled": bool(getattr(get_settings(), "mcp_bridge_enabled", False)),
        "tools": [
            {"name": "aethos_health", "description": "Provider skill registry snapshot.", "readonly": True},
            {"name": "aethos_chat_status", "description": "Execution plane and channel registry status.", "readonly": True},
            {"name": "aethos_local_skills", "description": "Operator skills from repo skills/ directory.", "readonly": True},
            {"name": "aethos_chat_turn", "description": "Resolve one governed chat turn.", "readonly": False},
        ],
    }


def invoke_mcp_tool(name: str, *, arguments: dict[str, Any] | None = None) -> dict[str, Any]:
    from aethos_core.config import get_settings

    args = dict(arguments or {})
    if not getattr(get_settings(), "mcp_bridge_enabled", False):
        return {"ok": False, "error": "mcp_bridge_disabled"}
    if name == "aethos_health":
        from aethos_core.operational_skill_runtime.skill_registry import skill_registry_snapshot

        return {"ok": True, "tool": name, "result": skill_registry_snapshot()}
    if name == "aethos_chat_status":
        from aethos_core.autonomous_execution.plane_service import plane_status_snapshot
        from aethos_core.channels.channel_registry import channel_registry_payload

        return {
            "ok": True,
            "tool": name,
            "result": {"execution_plane": plane_status_snapshot(), "channels": channel_registry_payload()},
        }
    if name == "aethos_local_skills":
        return {"ok": True, "tool": name, "result": local_operator_skills_snapshot()}
    if name == "aethos_chat_turn":
        text = str(args.get("text") or "").strip()
        if not text:
            return {"ok": False, "error": "text_required"}
        from aethos_core.chat.service import resolve_chat_turn

        result = resolve_chat_turn(text, session_id=str(args.get("session_id") or "mcp"), channel="mcp")
        return {
            "ok": True,
            "tool": name,
            "result": {
                "reply": result.reply,
                "intent": result.intent,
                "used_llm": result.used_llm,
                "meta": dict(getattr(result, "meta", None) or {}),
            },
        }
    return {"ok": False, "error": f"unknown_tool:{name}"}

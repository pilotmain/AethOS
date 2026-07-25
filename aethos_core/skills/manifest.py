# SPDX-License-Identifier: Apache-2.0
"""Skill manifests + governance classification — the trust foundation for a
governed skill marketplace.

Every operator skill is a SKILL.md playbook with YAML frontmatter and declared
tool sections (## Readonly tools / ## Mutation tools / ## Governance). This module
turns each one into an inspectable manifest with a risk classification, so a skill
can be reviewed BEFORE it is trusted/installed — the opposite of an open plugin
ecosystem where community code runs unreviewed. No code is executed here; this is
pure parsing + classification.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class SkillManifest:
    id: str
    name: str
    description: str = ""
    version: str = ""
    author: str = ""
    tags: tuple[str, ...] = ()
    readonly_tools: tuple[str, ...] = ()
    mutation_tools: tuple[str, ...] = ()
    mutates: bool = False
    risk: str = "read-only"  # "read-only" | "governed-mutation"
    requires_approval: bool = False

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "version": self.version,
            "author": self.author,
            "tags": list(self.tags),
            "readonly_tools": list(self.readonly_tools),
            "mutation_tools": list(self.mutation_tools),
            "mutates": self.mutates,
            "risk": self.risk,
            "requires_approval": self.requires_approval,
        }


def _frontmatter_value(content: str, key: str) -> str:
    """Read a YAML-frontmatter scalar, tolerant of a header before the first fence."""
    lines = content.splitlines()
    start = next((i for i, ln in enumerate(lines) if ln.strip() == "---"), None)
    if start is None:
        return ""
    for line in lines[start + 1 :]:
        if line.strip() == "---":
            break
        if line.strip().startswith(f"{key}:"):
            return line.split(":", 1)[1].strip().strip('"').strip("'")
    return ""


def _bullet_section(content: str, heading: str) -> list[str]:
    out: list[str] = []
    capture = False
    for line in content.splitlines():
        if line.strip().lower().startswith(f"## {heading.lower()}"):
            capture = True
            continue
        if capture and line.startswith("## "):
            break
        if capture and line.strip().startswith("- "):
            out.append(line.strip()[2:].strip())
    return out


def _section_text(content: str, heading: str) -> str:
    out: list[str] = []
    capture = False
    for line in content.splitlines():
        if line.strip().lower().startswith(f"## {heading.lower()}"):
            capture = True
            continue
        if capture and line.startswith("## "):
            break
        if capture:
            out.append(line)
    return "\n".join(out).strip()


def parse_skill_manifest(skill_id: str, content: str) -> SkillManifest:
    """Parse a SKILL.md into a manifest with a governance risk classification."""
    name = _frontmatter_value(content, "name") or skill_id
    description = _frontmatter_value(content, "description")
    version = _frontmatter_value(content, "version")
    author = _frontmatter_value(content, "author")
    raw_tags = _frontmatter_value(content, "tags")
    tags = tuple(t.strip() for t in raw_tags.replace("[", "").replace("]", "").split(",") if t.strip())

    readonly_tools = tuple(_bullet_section(content, "Readonly tools"))
    mutation_tools = tuple(_bullet_section(content, "Mutation tools"))
    governance = _section_text(content, "Governance").lower()

    # A skill is mutating if it declares Mutation tools (the reliable signal), or
    # its Governance section classifies it as a mutation. Honor explicit read-only
    # wording ("read-only", "no mutations") so it isn't a false positive. Mutating
    # skills are governed-mutation risk and require approval (existing preflight flow).
    declared_read_only = (
        "read-only" in governance or "readonly" in governance or "no mutation" in governance
    )
    mutates = bool(mutation_tools) or ("mutation" in governance and not declared_read_only)
    risk = "governed-mutation" if mutates else "read-only"

    return SkillManifest(
        id=skill_id,
        name=name,
        description=description,
        version=version,
        author=author,
        tags=tags,
        readonly_tools=readonly_tools,
        mutation_tools=mutation_tools,
        mutates=mutates,
        risk=risk,
        requires_approval=mutates,
    )


def governed_skill_catalog() -> dict[str, Any]:
    """All installed operator skills with parsed manifests + a governance summary.

    This is marketplace phase 1: skills are inspectable and risk-classified before
    they're trusted. (Remote registry, publish/install, and signing are later phases.)
    """
    from aethos_core.operational_skill_runtime.skill_loader import load_local_operator_skills
    from pathlib import Path

    catalog = load_local_operator_skills()
    skills: list[dict[str, Any]] = []
    for row in catalog.get("skills") or []:
        skill_id = str(row.get("id") or "")
        content = ""
        path = str(row.get("path") or "")
        if path:
            try:
                content = Path(path).read_text(encoding="utf-8")
            except OSError:
                content = ""
        skills.append(parse_skill_manifest(skill_id, content).to_dict())

    read_only = sum(1 for s in skills if not s["mutates"])
    governed_mutation = sum(1 for s in skills if s["mutates"])
    return {
        "ok": True,
        "count": len(skills),
        "skills": skills,
        "summary": {"read_only": read_only, "governed_mutation": governed_mutation},
        "governance": (
            "Every skill is reviewed before trust: read-only skills are safe; "
            "governed-mutation skills require approval before any action runs."
        ),
    }

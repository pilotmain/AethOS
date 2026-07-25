# SPDX-License-Identifier: Apache-2.0
"""Recall operator skills from repo skills/ — Skills registry read path."""

from __future__ import annotations

from typing import Any


def recall_skills(*, query: str = "", limit: int = 3) -> dict[str, Any]:
    # Gated behind SKILLS_REGISTRY_ENABLED (handoff §3/§21 step 5). Operator opts in,
    # mirroring the vector-memory recall gate. Default-off.
    from aethos_core.config import get_settings

    if not getattr(get_settings(), "skills_registry_enabled", False):
        return {"ok": False, "error": "skills_registry_disabled", "skills": []}
    from aethos_core.operational_skill_runtime.skill_loader import load_local_operator_skills

    catalog = load_local_operator_skills()
    skills = list(catalog.get("skills") or [])
    needle = (query or "").strip().lower()
    if needle:
        scored: list[tuple[int, dict[str, Any]]] = []
        for row in skills:
            hay = f"{row.get('id')} {row.get('name')} {row.get('description')}".lower()
            score = sum(1 for tok in needle.split() if tok in hay)
            if score:
                scored.append((score, row))
        scored.sort(key=lambda x: x[0], reverse=True)
        skills = [row for _, row in scored[: max(1, min(limit, 8))]]
    else:
        skills = skills[: max(1, min(limit, 8))]

    bodies: list[dict[str, Any]] = []
    for row in skills:
        path = str(row.get("path") or "")
        content = ""
        if path:
            try:
                from pathlib import Path

                content = Path(path).read_text(encoding="utf-8")[:4000]
            except OSError:
                content = ""
        bodies.append(
            {
                "id": row.get("id"),
                "name": row.get("name"),
                "description": row.get("description"),
                "content_excerpt": content,
            }
        )
    return {
        "ok": True,
        "query": query,
        "skill_count": len(bodies),
        "skills": bodies,
        "root": catalog.get("root"),
    }

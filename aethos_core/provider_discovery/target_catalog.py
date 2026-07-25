# SPDX-License-Identifier: Apache-2.0
"""Searchable provider service catalog."""

from __future__ import annotations

import re
from typing import Any

from aethos_core.provider_discovery.provider_inventory import ProviderInventory
from aethos_core.provider_discovery.provider_topology import format_service_path


def _normalize(text: str) -> str:
    return re.sub(r"\s+", " ", (text or "").strip().lower())


def _service_aliases(row: dict[str, Any]) -> list[str]:
    aliases = [str(a) for a in (row.get("aliases") or []) if a]
    name = str(row.get("service_name") or "")
    project = str(row.get("project_name") or "")
    if name:
        aliases.append(name)
        aliases.append(_normalize(name))
    if project and name:
        aliases.append(_normalize(f"{project} {name}"))
        aliases.append(_normalize(f"{project}-{name}"))
    return list(dict.fromkeys(_normalize(a) for a in aliases if a))


def build_target_catalog(inventory: ProviderInventory) -> list[dict[str, Any]]:
    catalog: list[dict[str, Any]] = []
    for row in inventory.all_services():
        catalog.append(
            {
                **row,
                "path": format_service_path(
                    project=str(row.get("project_name") or ""),
                    environment=str(row.get("environment") or "production"),
                    service=str(row.get("service_name") or ""),
                ),
                "search_aliases": _service_aliases(row),
            }
        )
    return catalog


def search_catalog(
    catalog: list[dict[str, Any]],
    *,
    phrase: str,
    project_hint: str | None = None,
    environment_hint: str | None = None,
) -> list[dict[str, Any]]:
    norm = _normalize(phrase)
    if not norm:
        return list(catalog)

    exact_alias: list[dict[str, Any]] = []
    for row in catalog:
        aliases = [_normalize(a) for a in (row.get("search_aliases") or [])]
        path = _normalize(str(row.get("path") or ""))
        if norm in aliases or norm == path or ("/" in norm and norm in path):
            exact_alias.append(row)
    if len(exact_alias) == 1:
        return exact_alias
    if len(exact_alias) > 1:
        return exact_alias

    matches: list[tuple[float, dict[str, Any]]] = []
    for row in catalog:
        score = 0.0
        name = _normalize(str(row.get("service_name") or ""))
        path = _normalize(str(row.get("path") or ""))
        aliases = [_normalize(a) for a in (row.get("search_aliases") or [])]
        if name == norm:
            score = 1.0
        elif norm in aliases:
            score = 0.98
        elif norm == _normalize(str(row.get("project_name") or "")):
            score = 0.2
        elif norm in name or name in norm:
            score = 0.86 if " " in norm or len(norm.split()) > 1 else 0.75
        elif any(norm in alias or alias in norm for alias in aliases):
            score = 0.82
        elif norm in path:
            score = 0.75
        if score <= 0:
            continue
        if project_hint and _normalize(project_hint) not in _normalize(str(row.get("project_name") or "")):
            score -= 0.15
        if environment_hint and _normalize(environment_hint) not in _normalize(str(row.get("environment") or "")):
            score -= 0.1
        matches.append((score, row))
    matches.sort(key=lambda item: item[0], reverse=True)
    return [row for _, row in matches]

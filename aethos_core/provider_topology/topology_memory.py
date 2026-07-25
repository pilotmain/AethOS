# SPDX-License-Identifier: Apache-2.0
"""Persist provider topology bindings and graph snapshots."""

from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from aethos_core.provider_topology.source_binding import SourceBinding
from aethos_core.provider_topology.topology_graph import ProviderTopologyGraph

_MEMORY: dict[str, SourceBinding] = {}
_GRAPH_CACHE: dict[str, ProviderTopologyGraph] = {}


def _store_dir() -> Path:
    root = Path(__file__).resolve().parents[2] / "data" / "provider_topology"
    root.mkdir(parents=True, exist_ok=True)
    return root


def _bindings_path() -> Path:
    return _store_dir() / "bindings.json"


def save_binding(binding: SourceBinding) -> dict[str, Any]:
    _MEMORY[binding.key] = binding
    all_bindings = load_all_bindings()
    all_bindings[binding.key] = binding
    payload = {key: row.to_dict() for key, row in all_bindings.items()}
    _bindings_path().write_text(json.dumps(payload, indent=2), encoding="utf-8")
    _GRAPH_CACHE.pop(binding.key, None)
    return {"ok": True, "binding_key": binding.key}


def load_all_bindings() -> dict[str, SourceBinding]:
    if _MEMORY:
        return dict(_MEMORY)
    path = _bindings_path()
    if not path.is_file():
        return {}
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}
    if not isinstance(raw, dict):
        return {}
    out: dict[str, SourceBinding] = {}
    for key, row in raw.items():
        if isinstance(row, dict):
            binding = SourceBinding.from_dict(row)
            out[str(key)] = binding
            _MEMORY[str(key)] = binding
    return out


def get_binding(*, provider: str, project: str, environment: str, service_name: str) -> SourceBinding | None:
    from aethos_core.provider_topology.source_binding import binding_key

    key = binding_key(provider=provider, project=project, environment=environment, service_name=service_name)
    bindings = load_all_bindings()
    return bindings.get(key)


def find_binding_by_service_name(service_name: str) -> SourceBinding | None:
    norm = (service_name or "").strip().lower()
    if not norm:
        return None
    for binding in load_all_bindings().values():
        if binding.service_name.lower() == norm:
            return binding
    return None


def cache_graph(graph: ProviderTopologyGraph) -> None:
    if graph.binding_key:
        _GRAPH_CACHE[graph.binding_key] = graph


def get_cached_graph(binding_key: str) -> ProviderTopologyGraph | None:
    return _GRAPH_CACHE.get(binding_key)


def clear_topology_for_tests() -> None:
    from aethos_core.provider_topology.binding_update_flow import clear_pending_corrections_for_tests
    from aethos_core.task_frame.pending_action import clear_pending_actions_for_tests

    _MEMORY.clear()
    _GRAPH_CACHE.clear()
    clear_pending_corrections_for_tests()
    clear_pending_actions_for_tests()
    path = _bindings_path()
    if path.is_file():
        path.unlink()

# SPDX-License-Identifier: Apache-2.0
"""Persisted provider inventory snapshots."""

from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from aethos_core.provider_discovery.provider_inventory import ProviderInventory

_MEMORY: dict[str, ProviderInventory] = {}


def _store_dir() -> Path:
    root = Path(__file__).resolve().parents[2] / "data" / "provider_inventory"
    root.mkdir(parents=True, exist_ok=True)
    return root


def _snapshot_path(provider: str) -> Path:
    safe = (provider or "unknown").strip().lower().replace("/", "_")
    return _store_dir() / f"{safe}.json"


def save_inventory_snapshot(inventory: ProviderInventory) -> dict[str, Any]:
    provider = inventory.provider
    _MEMORY[provider] = inventory
    payload = inventory.to_dict()
    path = _snapshot_path(provider)
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    return {"ok": True, "provider": provider, "path": str(path), "saved_at": datetime.now(UTC).isoformat()}


def load_inventory_snapshot(*, provider: str) -> ProviderInventory | None:
    provider = (provider or "").strip().lower()
    cached = _MEMORY.get(provider)
    if cached is not None:
        return cached
    path = _snapshot_path(provider)
    if not path.is_file():
        return None
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    if not isinstance(raw, dict):
        return None
    inventory = ProviderInventory.from_dict(raw)
    _MEMORY[provider] = inventory
    return inventory


def clear_inventory_memory_for_tests() -> None:
    _MEMORY.clear()
    path = _snapshot_path("railway")
    if path.is_file():
        path.unlink()
    for provider in ("vercel", "github", "docker", "kubernetes"):
        p = _snapshot_path(provider)
        if p.is_file():
            p.unlink()

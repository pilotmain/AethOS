# SPDX-License-Identifier: Apache-2.0
"""Durable Railway service creation execution simulation results."""

from __future__ import annotations

import json
import uuid
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

_STORE: dict[str, dict[str, Any]] = {}


def _without_repair_trace(simulation: dict[str, Any]) -> dict[str, Any]:
    payload = dict(simulation)
    payload.pop("normalized_stale_credential_blocker_repaired", None)
    return payload


def _store_dir() -> Path:
    root = Path(__file__).resolve().parents[3] / "data" / "railway_service_creation_simulation"
    root.mkdir(parents=True, exist_ok=True)
    return root


def _session_path(session_id: str) -> Path:
    safe = (session_id or "default").strip().replace("/", "_")[:128]
    return _store_dir() / f"{safe}_simulation.json"


def save_simulation(
    *,
    session_id: str,
    simulation: dict[str, Any],
    skip_lifecycle_sync: bool = False,
) -> None:
    session_id = (session_id or "default").strip()
    payload = dict(simulation)
    payload["updated_at"] = datetime.now(UTC).isoformat()
    if not payload.get("simulation_id"):
        payload["simulation_id"] = f"rsim-{uuid.uuid4().hex[:12]}"
    if not payload.get("created_at"):
        payload["created_at"] = payload["updated_at"]
    _STORE[session_id] = payload
    try:
        _session_path(session_id).write_text(json.dumps(payload, indent=2), encoding="utf-8")
    except OSError:
        pass
    if not skip_lifecycle_sync and payload.get("simulation_id"):
        from aethos_core.providers.railway.deployment_lifecycle.deployment_lifecycle_sync import (
            sync_lifecycle_after_simulation,
        )

        sync_lifecycle_after_simulation(session_id=session_id, simulation=payload)


def get_simulation(*, session_id: str) -> dict[str, Any] | None:
    from aethos_core.providers.railway.service_creation_simulator.simulator_normalization import (
        normalize_simulation_snapshot,
    )

    session_id = (session_id or "default").strip()
    cached = _STORE.get(session_id)
    if cached is not None:
        normalized, repaired = normalize_simulation_snapshot(dict(cached))
        if repaired:
            save_simulation(session_id=session_id, simulation=_without_repair_trace(normalized))
        if repaired or normalized.get("stale_lifecycle_blockers_repaired"):
            normalized = dict(normalized)
            normalized["normalized_stale_credential_blocker_repaired"] = True
        return normalized
    path = _session_path(session_id)
    if path.is_file():
        try:
            raw = json.loads(path.read_text(encoding="utf-8"))
            if isinstance(raw, dict) and raw.get("simulation_id"):
                normalized, repaired = normalize_simulation_snapshot(dict(raw))
                if repaired:
                    save_simulation(session_id=session_id, simulation=_without_repair_trace(normalized))
                if repaired or normalized.get("stale_lifecycle_blockers_repaired"):
                    normalized = dict(normalized)
                    normalized["normalized_stale_credential_blocker_repaired"] = True
                _STORE[session_id] = normalized
                return normalized
        except (OSError, json.JSONDecodeError):
            pass
    return None


def clear_simulation(*, session_id: str | None = None) -> None:
    if session_id:
        sid = session_id.strip()
        _STORE.pop(sid, None)
        try:
            _session_path(sid).unlink(missing_ok=True)
        except OSError:
            pass
        return
    _STORE.clear()


def clear_for_tests() -> None:
    clear_simulation()
    root = _store_dir()
    for path in root.glob("*.json"):
        path.unlink()

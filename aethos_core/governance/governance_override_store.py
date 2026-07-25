# SPDX-License-Identifier: Apache-2.0
"""Runtime governance overrides — MC kill switches without editing .env."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

_OVERRIDE_KEYS = frozenset(
    {
        "mutation_execution_enabled",
        "railway_greenfield_mutation_kill_switch",
    }
)


def governance_override_path() -> Path:
    from aethos_core.config import get_settings

    root = Path(get_settings().aethos_workspace_root or Path.cwd())
    return root / "data" / "governance_runtime_overrides.json"


def load_governance_overrides() -> dict[str, Any]:
    path = governance_override_path()
    if not path.is_file():
        return {}
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}
    if not isinstance(raw, dict):
        return {}
    return {k: raw[k] for k in _OVERRIDE_KEYS if k in raw}


def save_governance_override(*, key: str, value: bool, user: dict[str, Any] | None = None) -> dict[str, Any]:
    from aethos_core.config import get_settings
    from aethos_core.tenancy.operator import require_deployment_operator

    if get_settings().multi_tenant_enabled and not require_deployment_operator(user):
        raise PermissionError("deployment_operator_required")
    if key not in _OVERRIDE_KEYS:
        raise ValueError(f"Unsupported governance override: {key}")
    path = governance_override_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = load_governance_overrides()
    payload[key] = bool(value)
    payload["updated_at"] = datetime.now(timezone.utc).isoformat()
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return payload


def effective_bool_flag(key: str) -> bool:
    """Env default merged with runtime override when present."""
    from aethos_core.config import get_settings

    settings = get_settings()
    env_default = bool(getattr(settings, key, False))
    overrides = load_governance_overrides()
    if key in overrides:
        return bool(overrides[key])
    return env_default


def governance_override_snapshot() -> dict[str, Any]:
    overrides = load_governance_overrides()
    return {
        "path": str(governance_override_path()),
        "overrides": overrides,
        "effective": {
            "mutation_execution_enabled": effective_bool_flag("mutation_execution_enabled"),
            "railway_greenfield_mutation_kill_switch": effective_bool_flag(
                "railway_greenfield_mutation_kill_switch"
            ),
        },
    }

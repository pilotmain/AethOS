# SPDX-License-Identifier: Apache-2.0
"""Universal provider operations skill runtime."""

from __future__ import annotations

from typing import Any

_BOOTSTRAPPED = False
_BOOTSTRAP_SNAPSHOT: dict[str, Any] = {}


def bootstrap_operational_runtime(*, force: bool = False) -> dict[str, Any]:
    """Load identity contracts, provider skills, and operational memory context."""
    global _BOOTSTRAPPED, _BOOTSTRAP_SNAPSHOT
    if _BOOTSTRAPPED and not force:
        return dict(_BOOTSTRAP_SNAPSHOT)

    from aethos_core.aethos_identity.identity_contract_loader import get_identity_contract_status, load_identity_contracts
    from aethos_core.operational_skill_runtime.skill_loader import load_all_provider_skills
    from aethos_core.operational_skill_runtime.skill_registry import skill_registry_snapshot

    identity = load_identity_contracts(force_reload=force)
    skills = load_all_provider_skills(force=force)
    registry = skill_registry_snapshot()

    try:
        from aethos_core.operation_lifecycle.global_lifecycle_index import bootstrap_global_lifecycle_index

        bootstrap_global_lifecycle_index()
    except Exception:
        pass

    try:
        from aethos_core.providers.github.workflow_lane.workflow_lane_lifecycle import (
            bootstrap_workflow_lane_lifecycle,
        )

        bootstrap_workflow_lane_lifecycle()
    except Exception:
        pass

    _BOOTSTRAP_SNAPSHOT = {
        "ready": bool(identity.soul.exists and identity.memory.exists and skills.get("loaded_count", 0) > 0),
        "identity": get_identity_contract_status(),
        "skills": skills,
        "registry": registry,
    }
    _BOOTSTRAPPED = True
    return dict(_BOOTSTRAP_SNAPSHOT)


def is_operational_runtime_ready() -> bool:
    if not _BOOTSTRAPPED:
        bootstrap_operational_runtime()
    return bool(_BOOTSTRAP_SNAPSHOT.get("ready"))


def operational_runtime_status() -> dict[str, Any]:
    if not _BOOTSTRAPPED:
        bootstrap_operational_runtime()
    return dict(_BOOTSTRAP_SNAPSHOT)

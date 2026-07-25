# SPDX-License-Identifier: Apache-2.0
"""FIX 112 — configure_env contract models (groups, rollback plan)."""

from __future__ import annotations

from typing import Final

CONFIGURE_ENV_FORWARD_PHASE: Final[str] = "configure_env"
CONFIGURE_ENV_ROLLBACK_PHASE: Final[str] = "rollback_configure_env"
CONFIGURE_ENV_ROLLBACK_ACTION: Final[str] = "revert_env_writes"

# Receipts are recorded per group (never per secret value).
ENV_CONFIGURE_GROUP_MINIMUM_SECRETS: Final[str] = "minimum_secrets"
ENV_CONFIGURE_GROUP_UI_RUNTIME: Final[str] = "ui_runtime_vars"

ENV_CONFIGURE_GROUPS: Final[tuple[tuple[str, tuple[str, ...]], ...]] = (
    (ENV_CONFIGURE_GROUP_MINIMUM_SECRETS, ("ANTHROPIC_API_KEY", "WEB_SEARCH_API_KEY")),
)


def resolve_env_configure_groups(plan: dict[str, object] | None = None) -> tuple[tuple[str, tuple[str, ...]], ...]:
    """Return env configure groups for this deployment target (API vs Mission Control UI)."""
    if str((plan or {}).get("deploy_component") or "") == "ui":
        from aethos_core.providers.railway.greenfield_deployment.greenfield_deploy_component import (
            ui_required_env_var_names,
        )

        names = tuple(str(n).strip().upper() for n in ui_required_env_var_names() if str(n).strip())
        return ((ENV_CONFIGURE_GROUP_UI_RUNTIME, names),)
    return ENV_CONFIGURE_GROUPS


def required_env_names_for_plan(plan: dict[str, object] | None = None) -> tuple[str, ...]:
    names: list[str] = []
    for _group_id, group_names in resolve_env_configure_groups(plan):
        names.extend(str(n).upper() for n in group_names if str(n).strip())
    return tuple(names)

CONFIGURE_ENV_ROLLBACK_STEPS: Final[tuple[str, ...]] = (
    "verify_create_service_and_connect_source_live",
    "record_revert_env_writes_rollback_plan",
    "write_env_groups_from_secure_store",
    "record_configure_env_group_receipts",
    "verify_readonly_env_names_only",
)

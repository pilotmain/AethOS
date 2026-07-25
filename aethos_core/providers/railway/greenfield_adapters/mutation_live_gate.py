# SPDX-License-Identifier: Apache-2.0
"""
FIX 108B — Live mutation authorization gate.

`create_railway_service` must only run inside `live_create_service_authorization()`,
which the real-mutation executor sets. Dry-run and simulation paths never set this.
"""

from __future__ import annotations

from contextlib import contextmanager
from contextvars import ContextVar
from typing import Iterator

from aethos_core.providers.railway.greenfield_adapters.mutation_kill_switch import (
    is_railway_mutation_kill_switch_active,
)

_LIVE_CREATE_SERVICE_AUTHORIZED: ContextVar[bool] = ContextVar(
    "railway_live_create_service_authorized",
    default=False,
)
_LIVE_CONNECT_GITHUB_SOURCE_AUTHORIZED: ContextVar[bool] = ContextVar(
    "railway_live_connect_github_source_authorized",
    default=False,
)
_LIVE_DISCONNECT_GITHUB_SOURCE_AUTHORIZED: ContextVar[bool] = ContextVar(
    "railway_live_disconnect_github_source_authorized",
    default=False,
)
_LIVE_CONFIGURE_ENV_AUTHORIZED: ContextVar[bool] = ContextVar(
    "railway_live_configure_env_authorized",
    default=False,
)
_LIVE_REVERT_ENV_AUTHORIZED: ContextVar[bool] = ContextVar(
    "railway_live_revert_env_authorized",
    default=False,
)
_LIVE_TRIGGER_DEPLOY_AUTHORIZED: ContextVar[bool] = ContextVar(
    "railway_live_trigger_deploy_authorized",
    default=False,
)
_RUNTIME_VERIFICATION_AUTHORIZED: ContextVar[bool] = ContextVar(
    "railway_runtime_verification_authorized",
    default=False,
)


class LiveMutationNotAuthorizedError(RuntimeError):
    """Raised when create_railway_service is invoked outside the governed live path."""


class LiveMutationKillSwitchActiveError(RuntimeError):
    """Raised when emergency kill switch blocks live mutations."""


class LiveMutationModeError(RuntimeError):
    """Raised when runtime execution mode is not enabled for live mutations."""


@contextmanager
def live_create_service_authorization() -> Iterator[None]:
    """Grant temporary authorization for one governed create_service call."""
    token = _LIVE_CREATE_SERVICE_AUTHORIZED.set(True)
    try:
        yield
    finally:
        _LIVE_CREATE_SERVICE_AUTHORIZED.reset(token)


def is_live_create_service_authorized() -> bool:
    return bool(_LIVE_CREATE_SERVICE_AUTHORIZED.get())


def _enforce_common_live_mutation_policy(*, adapter_name: str) -> None:
    from aethos_core.providers.railway.execution_contract.execution_enablement import (
        load_railway_execution_enablement_config,
    )

    if is_railway_mutation_kill_switch_active():
        raise LiveMutationKillSwitchActiveError(
            "Railway greenfield mutation kill switch is active; live mutations are blocked."
        )
    cfg = load_railway_execution_enablement_config()
    if cfg.mode != "enabled":
        raise LiveMutationModeError(
            f"Live mutations require execution_mode=enabled (current: {cfg.mode})."
        )
    if not cfg.greenfield_execution_enabled:
        raise LiveMutationModeError(
            "Live mutations require railway_greenfield_execution_enabled=true."
        )
    _ = adapter_name


@contextmanager
def live_connect_github_source_authorization() -> Iterator[None]:
    """Grant temporary authorization for one governed connect_source call."""
    token = _LIVE_CONNECT_GITHUB_SOURCE_AUTHORIZED.set(True)
    try:
        yield
    finally:
        _LIVE_CONNECT_GITHUB_SOURCE_AUTHORIZED.reset(token)


def is_live_connect_github_source_authorized() -> bool:
    return bool(_LIVE_CONNECT_GITHUB_SOURCE_AUTHORIZED.get())


def require_live_create_service_authorization() -> None:
    """Enforce live-path-only access at the create_service adapter boundary."""
    if not is_live_create_service_authorized():
        raise LiveMutationNotAuthorizedError(
            "create_railway_service was called without live_create_service_authorization. "
            "Dry-run and simulation paths must not invoke the live mutation adapter."
        )
    _enforce_common_live_mutation_policy(adapter_name="create_service")


def require_live_connect_github_source_authorization() -> None:
    """Enforce live-path-only access at the connect_source adapter boundary."""
    if not is_live_connect_github_source_authorized():
        raise LiveMutationNotAuthorizedError(
            "connect_github_source was called without live_connect_github_source_authorization. "
            "Dry-run and simulation paths must not invoke the live mutation adapter."
        )
    _enforce_common_live_mutation_policy(adapter_name="connect_source")
    from aethos_core.config import get_settings

    if not bool(getattr(get_settings(), "railway_greenfield_connect_source_enabled", False)):
        raise LiveMutationModeError(
            "connect_source live mutations require railway_greenfield_connect_source_enabled=true."
        )


@contextmanager
def live_disconnect_github_source_authorization() -> Iterator[None]:
    """Grant temporary authorization for one governed disconnect_repo_source rollback."""
    token = _LIVE_DISCONNECT_GITHUB_SOURCE_AUTHORIZED.set(True)
    try:
        yield
    finally:
        _LIVE_DISCONNECT_GITHUB_SOURCE_AUTHORIZED.reset(token)


def is_live_disconnect_github_source_authorized() -> bool:
    return bool(_LIVE_DISCONNECT_GITHUB_SOURCE_AUTHORIZED.get())


def require_live_disconnect_github_source_authorization() -> None:
    """Enforce live-path-only access at the disconnect_repo_source rollback adapter."""
    if not is_live_disconnect_github_source_authorized():
        raise LiveMutationNotAuthorizedError(
            "disconnect_github_source was called without live_disconnect_github_source_authorization. "
            "Dry-run rollback paths must not invoke the live rollback adapter."
        )
    _enforce_common_live_mutation_policy(adapter_name="disconnect_repo_source")
    from aethos_core.config import get_settings

    if not bool(getattr(get_settings(), "railway_greenfield_disconnect_source_enabled", False)):
        raise LiveMutationModeError(
            "disconnect_source live rollback requires "
            "railway_greenfield_disconnect_source_enabled=true."
        )


@contextmanager
def live_revert_env_authorization() -> Iterator[None]:
    """Grant temporary authorization for one governed revert_env_writes rollback."""
    token = _LIVE_REVERT_ENV_AUTHORIZED.set(True)
    try:
        yield
    finally:
        _LIVE_REVERT_ENV_AUTHORIZED.reset(token)


def require_live_revert_env_authorization() -> None:
    """Enforce live-path-only access at the revert_env_writes rollback adapter."""
    if not _LIVE_REVERT_ENV_AUTHORIZED.get():
        raise LiveMutationNotAuthorizedError(
            "revert_env_writes was called without live_revert_env_authorization. "
            "Forward and dry-run paths must not invoke the live env rollback adapter."
        )
    _enforce_common_live_mutation_policy(adapter_name="revert_env_writes")
    from aethos_core.config import get_settings

    if not bool(getattr(get_settings(), "railway_greenfield_revert_env_enabled", False)):
        raise LiveMutationModeError(
            "revert_env_writes live rollback requires railway_greenfield_revert_env_enabled=true."
        )


@contextmanager
def live_configure_env_authorization() -> Iterator[None]:
    """Grant temporary authorization for one governed configure_env group write."""
    token = _LIVE_CONFIGURE_ENV_AUTHORIZED.set(True)
    try:
        yield
    finally:
        _LIVE_CONFIGURE_ENV_AUTHORIZED.reset(token)


def is_live_configure_env_authorized() -> bool:
    return bool(_LIVE_CONFIGURE_ENV_AUTHORIZED.get())


def require_live_configure_env_authorization() -> None:
    """Enforce live-path-only access at the configure_env adapter boundary."""
    if not is_live_configure_env_authorized():
        raise LiveMutationNotAuthorizedError(
            "configure_env_group was called without live_configure_env_authorization. "
            "Dry-run paths must not invoke the live env write adapter."
        )
    _enforce_common_live_mutation_policy(adapter_name="configure_env")
    from aethos_core.config import get_settings

    if not bool(getattr(get_settings(), "railway_greenfield_configure_env_enabled", False)):
        raise LiveMutationModeError(
            "configure_env live writes require railway_greenfield_configure_env_enabled=true."
        )


@contextmanager
def live_trigger_deploy_authorization() -> Iterator[None]:
    """Grant temporary authorization for one governed trigger_deploy call."""
    token = _LIVE_TRIGGER_DEPLOY_AUTHORIZED.set(True)
    try:
        yield
    finally:
        _LIVE_TRIGGER_DEPLOY_AUTHORIZED.reset(token)


def is_live_trigger_deploy_authorized() -> bool:
    return bool(_LIVE_TRIGGER_DEPLOY_AUTHORIZED.get())


def require_live_trigger_deploy_authorization() -> None:
    """Enforce live-path-only access at the trigger_deploy adapter boundary."""
    if not is_live_trigger_deploy_authorized():
        raise LiveMutationNotAuthorizedError(
            "trigger_railway_deploy was called without live_trigger_deploy_authorization. "
            "Dry-run paths must not invoke the live deploy trigger adapter."
        )
    _enforce_common_live_mutation_policy(adapter_name="trigger_deploy")
    from aethos_core.config import get_settings

    if not bool(getattr(get_settings(), "railway_greenfield_trigger_deploy_enabled", False)):
        raise LiveMutationModeError(
            "trigger_deploy live mutations require railway_greenfield_trigger_deploy_enabled=true."
        )


@contextmanager
def runtime_verification_authorization() -> Iterator[None]:
    """Grant temporary authorization for one governed readonly verify_runtime check."""
    token = _RUNTIME_VERIFICATION_AUTHORIZED.set(True)
    try:
        yield
    finally:
        _RUNTIME_VERIFICATION_AUTHORIZED.reset(token)


def require_runtime_verification_authorization() -> None:
    """Enforce governed-path-only access at the readonly verify_runtime adapter."""
    if not _RUNTIME_VERIFICATION_AUTHORIZED.get():
        raise LiveMutationNotAuthorizedError(
            "verify_runtime_readonly was called without runtime_verification_authorization. "
            "Ungoverned paths must not invoke runtime verification."
        )
    _enforce_common_live_mutation_policy(adapter_name="verify_runtime")
    from aethos_core.config import get_settings

    if not bool(getattr(get_settings(), "railway_greenfield_verify_runtime_enabled", False)):
        raise LiveMutationModeError(
            "verify_runtime requires railway_greenfield_verify_runtime_enabled=true."
        )

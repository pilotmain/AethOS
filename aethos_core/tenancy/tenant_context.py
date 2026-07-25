# SPDX-License-Identifier: Apache-2.0
"""Tenant context primitives — ContextVar, scope manager, and resolution.

Deliberately dependency-free (no FastAPI, no settings import at module load) so
it is safe to import from anywhere, including hot resolver paths and background
threads.
"""

from __future__ import annotations

from collections.abc import Iterator
from contextlib import contextmanager
from contextvars import ContextVar, Token

# The operator/single-tenant identity. Used whenever multi-tenancy is off, or
# when no explicit tenant has been established. Stable and never empty.
DEFAULT_TENANT = "default"

# Request-scoped only. Set by tenant_context_middleware for in-request handlers,
# and by tenant_scope() inside detached work. Default None ⇒ "no tenant bound",
# which resolves to DEFAULT_TENANT. Never read this directly from detached work
# without first establishing a scope from the work's stamped tenant_id.
_current_tenant: ContextVar[str | None] = ContextVar("aethos_current_tenant", default=None)


def normalize_tenant(value: object) -> str:
    """Coerce an arbitrary value into a non-empty tenant id (or DEFAULT_TENANT).

    Tenant ids are derived from the auth user id (an email, lowercased). We keep
    this permissive but defensive: anything falsy or whitespace-only ⇒ default.
    """
    if value is None:
        return DEFAULT_TENANT
    text = str(value).strip().lower()
    return text or DEFAULT_TENANT


def set_current_tenant(tenant_id: object) -> Token[str | None]:
    """Bind the current tenant for this context; returns a token for reset()."""
    return _current_tenant.set(normalize_tenant(tenant_id))


def reset_current_tenant(token: Token[str | None]) -> None:
    """Restore the previous tenant binding (pair with set_current_tenant)."""
    try:
        _current_tenant.reset(token)
    except (ValueError, LookupError):
        # Token created in a different context (e.g. crossed a thread boundary);
        # clearing to None is the safe fallback.
        _current_tenant.set(None)


def get_current_tenant() -> str:
    """The tenant bound to the current context, or DEFAULT_TENANT if none.

    Safe to call anywhere. In a detached thread with no scope established this
    returns DEFAULT_TENANT — which is why detached work must wrap itself in
    ``tenant_scope(stamped_tenant_id)`` before any resolver runs.
    """
    return _current_tenant.get() or DEFAULT_TENANT


def current_tenant_or_default() -> str:
    """Alias kept for readability at call sites that want the intent spelled out."""
    return get_current_tenant()


def resolve_tenant(explicit: object | None = None) -> str:
    """Resolve the effective tenant, preferring an explicit stamp.

    Resolution order (Correction 1): an explicit, non-default ``tenant_id``
    (e.g. a durable job's or arbiter session's stamp) wins over the request
    ContextVar, which wins over DEFAULT_TENANT. Detached resolvers pass the
    work's stamped tenant_id here; in-request resolvers pass None.
    """
    if explicit is not None:
        normalized = normalize_tenant(explicit)
        if normalized != DEFAULT_TENANT:
            return normalized
    return get_current_tenant()


@contextmanager
def tenant_scope(tenant_id: object) -> Iterator[str]:
    """Bind ``tenant_id`` for the duration of the block, then restore.

    The building block detached work uses to re-establish its owning tenant:

        with tenant_scope(job["tenant_id"]):
            ...  # resolvers here see the job's tenant, not the request's

    Works across thread/task boundaries because it sets the ContextVar inside the
    new context rather than relying on inheritance.
    """
    token = set_current_tenant(tenant_id)
    try:
        yield get_current_tenant()
    finally:
        reset_current_tenant(token)

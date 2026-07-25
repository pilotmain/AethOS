# SPDX-License-Identifier: Apache-2.0
"""AethOS tenancy — per-request tenant identity + detached-work tenant binding.

This package is the single source of truth for "whose request/job is this?".

Two distinct mechanisms, by design (see MULTI_TENANT_PLAN.md, Correction 1):

  * **In-request handlers** read a request-scoped ``ContextVar`` via
    ``get_current_tenant()``. ``tenant_context_middleware`` sets it from the
    authenticated user for the lifetime of the request and resets it after.

  * **Detached work** (durable jobs that run in a background thread, arbiter
    sessions that fan out across executor threads) has **no live request
    context**, so a ContextVar lookup there would be empty or — worse — leak a
    different tenant. Such work is stamped with an explicit ``tenant_id`` at
    creation time and re-establishes the tenant with ``tenant_scope(tenant_id)``
    inside the detached context. Resolvers there read the job's/session's stamp,
    never the request ContextVar.

When ``MULTI_TENANT_ENABLED`` is off, everything resolves to ``DEFAULT_TENANT``
so existing single-tenant code is byte-for-byte unchanged.
"""

from __future__ import annotations

from aethos_core.tenancy.tenant_context import (
    DEFAULT_TENANT,
    current_tenant_or_default,
    get_current_tenant,
    normalize_tenant,
    reset_current_tenant,
    resolve_tenant,
    set_current_tenant,
    tenant_scope,
)

__all__ = [
    "DEFAULT_TENANT",
    "current_tenant_or_default",
    "get_current_tenant",
    "normalize_tenant",
    "reset_current_tenant",
    "resolve_tenant",
    "set_current_tenant",
    "tenant_scope",
]

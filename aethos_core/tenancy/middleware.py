# SPDX-License-Identifier: Apache-2.0
"""tenant_context_middleware — bind the request's tenant for in-request handlers.

Registered so it runs *after* the auth middleware (which sets
``request.state.user``) and wraps the route handler. For the lifetime of the
request the ``current_tenant`` ContextVar is the authenticated user's tenant;
it is reset afterwards so nothing leaks between requests.

No-op when ``MULTI_TENANT_ENABLED`` is off: the tenant resolves to
``DEFAULT_TENANT`` and behavior is unchanged.
"""

from __future__ import annotations

from aethos_core.tenancy.tenant_context import (
    DEFAULT_TENANT,
    reset_current_tenant,
    set_current_tenant,
)


def tenant_for_request(request) -> str:
    """Derive the tenant id for a request from its authenticated user.

    Single-tenant (flag off) ⇒ DEFAULT_TENANT. Multi-tenant ⇒ the user id set by
    the auth middleware (``request.state.user``); anonymous requests that slip
    through (open paths) also map to DEFAULT_TENANT, never another tenant.
    """
    from aethos_core.config import get_settings

    if not get_settings().multi_tenant_enabled:
        return DEFAULT_TENANT
    user = getattr(request.state, "user", None)
    if not user:
        return DEFAULT_TENANT
    return str(user.get("user_id") or user.get("email") or DEFAULT_TENANT)


async def tenant_context_middleware(request, call_next):
    """Set the current-tenant ContextVar for the request, then reset it."""
    from aethos_core.config import get_settings

    tenant = tenant_for_request(request)
    token = set_current_tenant(tenant)
    try:
        if get_settings().multi_tenant_enabled:
            user = getattr(request.state, "user", None)
            if user and tenant:
                from aethos_core.orgs.tenant_bridge import ensure_tenant_org

                ensure_tenant_org(
                    tenant,
                    display_name=str(user.get("name") or user.get("email") or tenant),
                    auth_roles=user.get("roles"),
                )
        response = await call_next(request)
    finally:
        reset_current_tenant(token)
    return response

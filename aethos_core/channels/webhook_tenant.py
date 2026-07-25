# SPDX-License-Identifier: Apache-2.0
"""Tenant binding for inbound channel webhooks (no browser session cookie)."""

from __future__ import annotations

from collections.abc import Iterator
from contextlib import contextmanager

from aethos_core.tenancy import DEFAULT_TENANT, tenant_scope


@contextmanager
def channel_webhook_tenant_scope(provider: str) -> Iterator[str]:
    """Resolve vault owner for a channel provider and bind tenant context for the webhook."""
    from aethos_core.config import get_settings
    from aethos_core.security.credential_vault import get_credential_vault

    if not get_settings().multi_tenant_enabled:
        with tenant_scope(DEFAULT_TENANT) as tenant:
            yield tenant
        return

    owner = get_credential_vault().find_unique_owner_for_provider(provider)
    tenant = owner or DEFAULT_TENANT
    with tenant_scope(tenant) as bound:
        yield bound

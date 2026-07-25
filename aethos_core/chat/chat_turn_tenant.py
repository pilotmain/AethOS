# SPDX-License-Identifier: Apache-2.0
"""Tenant binding for chat turns — Correction 1 for the chat agent path.

HTTP middleware sets the tenant ContextVar for in-request handlers, but chat
streaming with live progress runs the governed pipeline in a background thread
that does not inherit ContextVars. Detached durable jobs already stamp tenant_id
on the job record; chat must explicitly capture the originating tenant at the
API boundary and re-establish it inside worker threads and the agent tool loop.
"""

from __future__ import annotations

from contextlib import contextmanager
from typing import Iterator

from aethos_core.tenancy import DEFAULT_TENANT, get_current_tenant, normalize_tenant, tenant_scope


def resolve_chat_turn_tenant(explicit: str | None = None) -> str:
    """Tenant id for the current chat turn (explicit stamp or request ContextVar)."""
    if explicit:
        normalized = normalize_tenant(explicit)
        return normalized or DEFAULT_TENANT
    return get_current_tenant()


@contextmanager
def chat_turn_scope(tenant_id: str | None = None) -> Iterator[str]:
    """Re-establish tenant scope for a chat turn or detached chat worker."""
    tid = resolve_chat_turn_tenant(tenant_id)
    with tenant_scope(tid):
        yield tid

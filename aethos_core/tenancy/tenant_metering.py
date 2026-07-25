# SPDX-License-Identifier: Apache-2.0
"""Per-tenant usage metering and quotas (Phase 6).

Reuses the org-scoped metering ledger (already per-tenant via org bridge) and
adds an explicit daily token counter for operator-configured ceilings.
"""

from __future__ import annotations

import time
from typing import Any

_NS = "tenant_metering"


def _settings() -> Any:
    from aethos_core.config import get_settings

    return get_settings()


def _tenant(tenant_id: str | None = None) -> str:
    from aethos_core.tenancy.tenant_data_store import resolve_data_tenant

    return resolve_data_tenant(tenant_id)


def _day_key() -> str:
    return time.strftime("%Y-%m-%d", time.gmtime())


def _seconds_until_utc_midnight() -> int:
    now = time.gmtime()
    elapsed = now.tm_hour * 3600 + now.tm_min * 60 + now.tm_sec
    return max(60, 86400 - elapsed)


def record_llm_tokens(
    tokens: int, *, tenant_id: str | None = None, input_tokens: int = 0, output_tokens: int = 0
) -> None:
    """Increment the tenant's rolling daily token counter."""
    amount = int(tokens or 0) or int(input_tokens or 0) + int(output_tokens or 0)
    if amount <= 0:
        return
    from aethos_core.tenancy.tenant_data_store import get_record, set_record

    tid = _tenant(tenant_id)
    key = _day_key()
    current = int(get_record(_NS, key, tenant_id=tid, default=0) or 0)
    set_record(_NS, key, current + amount, tenant_id=tid)


def daily_token_usage(*, tenant_id: str | None = None) -> int:
    from aethos_core.tenancy.tenant_data_store import get_record

    return int(get_record(_NS, _day_key(), tenant_id=_tenant(tenant_id), default=0) or 0)


def check_llm_token_quota(*, tenant_id: str | None = None) -> tuple[bool, int]:
    """Return (allowed, retry_after_sec). Operator/default tenant is exempt."""
    s = _settings()
    limit = int(getattr(s, "tenant_llm_tokens_per_day", 0) or 0)
    if limit <= 0 or not s.multi_tenant_enabled:
        return True, 0
    from aethos_core.tenancy import DEFAULT_TENANT

    tid = _tenant(tenant_id)
    if tid == DEFAULT_TENANT:
        return True, 0
    used = daily_token_usage(tenant_id=tid)
    if used >= limit:
        return False, _seconds_until_utc_midnight()
    return True, 0


def get_tenant_usage_summary(*, tenant_id: str | None = None, session_id: str | None = None) -> dict[str, Any]:
    """Usage snapshot for the tenant onboarding / settings surfaces."""
    from aethos_core.observability.metering import get_usage_summary
    from aethos_core.tenancy import DEFAULT_TENANT

    tid = _tenant(tenant_id)
    org_summary = get_usage_summary(session_id=session_id)
    limit = int(getattr(_settings(), "tenant_llm_tokens_per_day", 0) or 0)
    used = daily_token_usage(tenant_id=tid)
    allowed, retry_after = check_llm_token_quota(tenant_id=tid)
    return {
        "ok": True,
        "tenant_id": tid,
        "operator_exempt": tid == DEFAULT_TENANT,
        "daily_tokens": {"used": used, "limit": limit or None, "quota_ok": allowed, "retry_after_sec": retry_after},
        "org_usage": org_summary,
    }

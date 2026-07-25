# SPDX-License-Identifier: Apache-2.0
"""Tenant-scoped paths for hosted GitHub workspace caches."""

from __future__ import annotations

import os
import re
from pathlib import Path

_SAFE = re.compile(r"[^a-zA-Z0-9._@-]+")


def _tenant_slug(tenant_id: str) -> str:
    slug = _SAFE.sub("-", str(tenant_id or "default").strip().lower()).strip("-")
    return slug[:120] or "default"


def remote_workspace_cache_root() -> Path:
    raw = str(os.environ.get("REMOTE_WORKSPACE_CACHE_DIR", "") or "").strip()
    if raw:
        root = Path(raw).expanduser().resolve()
    else:
        from aethos_core.aethos_identity.identity_contract_loader import repo_root

        root = (repo_root() / "data" / "remote_workspace_cache").resolve()
    root.mkdir(parents=True, exist_ok=True)
    return root


def github_clone_dir(repository: str, *, tenant_id: str | None = None) -> Path:
    from aethos_core.tenancy import get_current_tenant

    tid = tenant_id or get_current_tenant()
    safe_repo = repository.replace("/", "__")
    return remote_workspace_cache_root() / _tenant_slug(tid) / safe_repo

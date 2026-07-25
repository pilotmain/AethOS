# SPDX-License-Identifier: Apache-2.0
"""Shared store backend selection — Postgres when DATABASE_URL is set, else local files."""

from __future__ import annotations

import os


def database_url() -> str:
    return str(
        os.environ.get("DATABASE_URL", "") or os.environ.get("POSTGRES_URL", "") or ""
    ).strip()


def uses_postgres_shared_store() -> bool:
    return bool(database_url())


def shared_store_backend_label() -> str:
    if uses_postgres_shared_store():
        return "postgres"
    from aethos_core.production.deployment_mode import is_hosted_deployment

    if is_hosted_deployment():
        return "tenant_sqlite"
    return "local_file"

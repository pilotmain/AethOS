# SPDX-License-Identifier: Apache-2.0
"""Vercel env metadata reader — keys and targets only."""

from __future__ import annotations

from typing import Any

from aethos_core.providers.vercel.operations.env_metadata_api import fetch_env_metadata


def read_env_metadata(token: str, *, project_name: str) -> dict[str, Any]:
    payload = fetch_env_metadata(token, project_name=project_name)
    if not payload.get("ok"):
        return payload
    keys = [str(row.get("key") or "") for row in payload.get("env_metadata") or [] if isinstance(row, dict)]
    targets = sorted({str(row.get("target") or "") for row in payload.get("env_metadata") or [] if isinstance(row, dict)})
    return {
        **payload,
        "keys": keys,
        "targets": targets,
    }

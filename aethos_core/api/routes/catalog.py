# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

from typing import Any

from fastapi import APIRouter

router = APIRouter(tags=["catalog"])


@router.get("/catalog/connections")
def get_connections_catalog() -> dict[str, Any]:
    from aethos_core.catalog.connection_catalog import build_connections_catalog

    return build_connections_catalog()

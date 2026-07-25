# SPDX-License-Identifier: Apache-2.0
"""Deprecated setup/auth probes — compatibility shims until all callers are removed."""

from __future__ import annotations

from fastapi import APIRouter

router = APIRouter(tags=["legacy"])


@router.get("/auth/ping")
def legacy_auth_ping() -> dict[str, bool | str]:
    return {"ok": True, "deprecated": True}


@router.get("/setup/auth-diagnostics")
def legacy_setup_auth_diagnostics() -> dict[str, bool | str]:
    return {"ok": True, "deprecated": True}


@router.get("/setup-creds")
def legacy_setup_creds() -> dict[str, bool | str]:
    return {"ok": True, "deprecated": True}

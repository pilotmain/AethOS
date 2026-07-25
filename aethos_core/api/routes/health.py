# SPDX-License-Identifier: Apache-2.0

from fastapi import APIRouter

from aethos_core.runtime.authority import authority

router = APIRouter(tags=["health"])


def resolve_deploy_version() -> str:
    """Build id for /version — APP_VERSION, else Railway commit SHA, else fallback."""
    import os

    from aethos_core.config import get_settings

    s = get_settings()
    explicit = (s.app_version or "").strip()
    railway = os.getenv("RAILWAY_GIT_COMMIT_SHA", "").strip()
    if explicit:
        return explicit
    if railway:
        return railway
    return "0.2.0"


@router.get("/version")
def get_app_version() -> dict[str, str]:
    from aethos_core.config import get_settings

    s = get_settings()
    version = resolve_deploy_version()
    # Hard block only when operator explicitly sets MIN_SUPPORTED_APP_VERSION.
    min_supported = (s.min_supported_app_version or "").strip()
    return {"version": version, "min_supported": min_supported}


@router.get("/health")
def get_health() -> dict[str, object]:
    from aethos_core.config import get_settings

    get_settings()
    snap = authority.snapshot()
    return {
        "status": "ok" if snap.transport.value == "reachable" else "degraded",
        "chat_ready": snap.chat_ready,
        "label": snap.label,
        "transport": snap.transport.value,
        "auth": snap.auth.value,
        "panel": snap.panel.value,
        "capabilities": authority.capabilities,
    }

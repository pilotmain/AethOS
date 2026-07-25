# SPDX-License-Identifier: Apache-2.0
"""Edge runtime — offline operational node."""

from __future__ import annotations

from time import time
from typing import Any

from aethos_core.config import get_settings


def get_edge_runtime_status() -> dict[str, Any]:
    """Edge runtime status — offline-capable operational node."""
    s = get_settings()
    enabled = getattr(s, "edge_runtime_enabled", False) or getattr(s, "deployment_mode", "") == "edge"
    return {
        "ok": True,
        "edge_enabled": enabled,
        "offline_mode": enabled,
        "local_evidence_cache": s.browser_artifacts_dir,
        "local_vault": s.credentials_dir,
        "sync_status": "delayed" if enabled else "n/a",
        "limited_intelligence": enabled,
        "capabilities": {
            "offline_operational_mode": enabled,
            "delayed_synchronization": enabled,
            "local_encrypted_vault": True,
            "cloud_dependency": not enabled,
        },
        "checked_at": time(),
    }


def get_hosted_cloud_status() -> dict[str, Any]:
    s = get_settings()
    enabled = getattr(s, "hosted_cloud_enabled", False) or getattr(s, "deployment_mode", "") == "hosted"
    return {
        "ok": True,
        "hosted_enabled": enabled,
        "managed_onboarding": enabled,
        "tenant_separation": True,
        "secure_update_channel": enabled,
        "centralized_observability": enabled,
    }

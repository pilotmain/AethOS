# SPDX-License-Identifier: Apache-2.0
"""P4.4 — vault-backed kubeconfig readonly stub."""

from __future__ import annotations

from typing import Any


def resolve_vault_kubeconfig_readonly(*, credential_id: str = "") -> dict[str, Any]:
    from aethos_core.config import get_settings

    if not bool(getattr(get_settings(), "kubernetes_vault_kubeconfig_enabled", False)):
        return {
            "ok": False,
            "error": "Kubernetes vault kubeconfig is disabled. Set KUBERNETES_VAULT_KUBECONFIG_ENABLED=true.",
        }
    try:
        from aethos_core.security.credential_vault import get_credential_vault

        vault = get_credential_vault()
        recs = vault.list_credentials(provider="kubernetes")
        if credential_id:
            recs = [r for r in recs if r.credential_id == credential_id]
        if not recs:
            return {"ok": False, "error": "No kubernetes kubeconfig credential stored in vault."}
        return {
            "ok": True,
            "credential_id": recs[0].credential_id,
            "message": "Kubeconfig resolved from vault metadata only; kubectl readonly wiring is a follow-up.",
        }
    except Exception as exc:
        return {"ok": False, "error": str(exc)}

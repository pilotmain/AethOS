# SPDX-License-Identifier: Apache-2.0
"""Supabase Management API adapter (handoff §3).

One account-level Personal Access Token (PAT) works across ALL of the operator's
Supabase projects. This adapter uses the Management API (https://api.supabase.com)
to enumerate projects, fetch a project's data-plane keys on demand, and create
projects for governed provisioning. The PAT is resolved from the encrypted vault
(provider "supabase") first, then the SUPABASE_ACCESS_TOKEN env field.

Network-facing calls are gated behind PROVISIONING_ORCHESTRATION_ENABLED. The
service_role key returned by get_project_keys is a high-sensitivity secret — it
is vault/secure-store only and must never be surfaced to chat or canvas.
"""

from __future__ import annotations

from typing import Any

import httpx

MANAGEMENT_API_BASE = "https://api.supabase.com"
_TIMEOUT_SEC = 20.0


def management_enabled() -> bool:
    """Network-facing Management API calls require the provisioning flag."""
    from aethos_core.config import get_settings

    return bool(getattr(get_settings(), "provisioning_orchestration_enabled", False))


def resolve_access_token() -> str:
    """Account-wide Supabase PAT: encrypted vault (provider 'supabase') → env.

    Never logged. The vault path matches every other provider token; only the
    most recent decryptable api_token credential is used.
    """
    try:
        from aethos_core.connections.credential_state import resolve_credential_state
        from aethos_core.credentials.provider_alias_resolution import list_credentials_for_canonical
        from aethos_core.security.credential_vault import get_credential_vault

        for cred in list_credentials_for_canonical("supabase"):
            if cred.revoked or cred.type.value != "api_token":
                continue
            if resolve_credential_state(cred.credential_id).get("decryptable"):
                secret = get_credential_vault().retrieve_secret(cred.credential_id) or {}
                token = str(secret.get("token") or "").strip()
                if token:
                    return token
    except Exception:  # noqa: BLE001 — vault optional; fall back to env
        pass
    from aethos_core.config import get_settings

    return str(getattr(get_settings(), "supabase_access_token", "") or "").strip()


def has_management_token() -> bool:
    return bool(resolve_access_token())


def _headers(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}", "Accept": "application/json"}


def _guard() -> tuple[str, dict[str, Any] | None]:
    """Return (token, error). error is non-None when the call cannot proceed."""
    if not management_enabled():
        return "", {
            "ok": False,
            "error": "provisioning_disabled",
            "detail": "Supabase Management API is gated — set PROVISIONING_ORCHESTRATION_ENABLED=true.",
        }
    token = resolve_access_token()
    if not token:
        return "", {
            "ok": False,
            "error": "no_management_token",
            "detail": "No Supabase access token — add a Personal Access Token in Mission Control → Advanced settings → Credentials.",
        }
    return token, None


def _project_url(ref: str) -> str:
    ref = (ref or "").strip()
    return f"https://{ref}.supabase.co" if ref else ""


def list_projects() -> dict[str, Any]:
    """GET /v1/projects — every project the PAT can see (account-wide)."""
    token, err = _guard()
    if err:
        return {**err, "projects": [], "count": 0}
    try:
        with httpx.Client(timeout=_TIMEOUT_SEC) as client:
            resp = client.get(f"{MANAGEMENT_API_BASE}/v1/projects", headers=_headers(token))
    except httpx.HTTPError as exc:
        return {"ok": False, "error": "request_failed", "detail": f"Supabase request failed: {exc}", "projects": [], "count": 0}
    if resp.status_code >= 400:
        return {
            "ok": False,
            "error": "rejected",
            "detail": f"Supabase Management API rejected the token (HTTP {resp.status_code}).",
            "http_status": resp.status_code,
            "projects": [],
            "count": 0,
        }
    try:
        raw = resp.json()
    except ValueError:
        return {"ok": False, "error": "bad_response", "detail": "Unexpected response from Supabase.", "projects": [], "count": 0}
    items = raw if isinstance(raw, list) else (raw.get("projects") if isinstance(raw, dict) else []) or []
    projects = []
    for p in items:
        if not isinstance(p, dict):
            continue
        ref = str(p.get("id") or p.get("ref") or "").strip()
        projects.append(
            {
                "ref": ref,
                "name": str(p.get("name") or ""),
                "region": str(p.get("region") or ""),
                "organization_id": str(p.get("organization_id") or ""),
                "status": str(p.get("status") or ""),
                "url": _project_url(ref),
                "created_at": p.get("created_at"),
            }
        )
    return {"ok": True, "projects": projects, "count": len(projects)}


def get_project_keys(ref: str) -> dict[str, Any]:
    """GET /v1/projects/{ref}/api-keys — fetch anon/service_role ON DEMAND.

    service_role is high-sensitivity (vault-only; never to chat/canvas). Keys are
    fetched per-call so secrets are not all cached up front.
    """
    ref = (ref or "").strip()
    if not ref:
        return {"ok": False, "error": "missing_ref", "detail": "A Supabase project ref is required."}
    token, err = _guard()
    if err:
        return err
    try:
        with httpx.Client(timeout=_TIMEOUT_SEC) as client:
            resp = client.get(f"{MANAGEMENT_API_BASE}/v1/projects/{ref}/api-keys", headers=_headers(token))
    except httpx.HTTPError as exc:
        return {"ok": False, "error": "request_failed", "detail": f"Supabase request failed: {exc}"}
    if resp.status_code >= 400:
        return {
            "ok": False,
            "error": "rejected",
            "detail": f"Could not read keys for project `{ref}` (HTTP {resp.status_code}).",
            "http_status": resp.status_code,
        }
    try:
        raw = resp.json()
    except ValueError:
        return {"ok": False, "error": "bad_response", "detail": "Unexpected response from Supabase."}
    keys = raw if isinstance(raw, list) else (raw.get("api_keys") if isinstance(raw, dict) else []) or []
    anon = ""
    service_role = ""
    for k in keys:
        if not isinstance(k, dict):
            continue
        name = str(k.get("name") or "").strip().lower()
        value = str(k.get("api_key") or k.get("key") or "").strip()
        if name == "anon":
            anon = value
        elif name == "service_role":
            service_role = value
    return {
        "ok": True,
        "ref": ref,
        "url": _project_url(ref),
        "anon_key": anon,
        "service_role_key": service_role,
        "has_service_role": bool(service_role),
    }


def create_project(
    *,
    name: str,
    organization_id: str,
    region: str,
    db_pass: str,
    plan: str = "free",
) -> dict[str, Any]:
    """POST /v1/projects — provision a new project (governed; callers create a
    Mission Control preflight before invoking this)."""
    if not (name or "").strip() or not (organization_id or "").strip():
        return {"ok": False, "error": "missing_fields", "detail": "Project name and organization_id are required."}
    token, err = _guard()
    if err:
        return err
    body = {
        "name": name.strip(),
        "organization_id": organization_id.strip(),
        "region": (region or "us-east-1").strip(),
        "db_pass": db_pass,
        "plan": (plan or "free").strip(),
    }
    try:
        with httpx.Client(timeout=_TIMEOUT_SEC) as client:
            resp = client.post(f"{MANAGEMENT_API_BASE}/v1/projects", headers=_headers(token), json=body)
    except httpx.HTTPError as exc:
        return {"ok": False, "error": "request_failed", "detail": f"Supabase request failed: {exc}"}
    if resp.status_code >= 400:
        return {
            "ok": False,
            "error": "rejected",
            "detail": f"Supabase project creation failed (HTTP {resp.status_code}).",
            "http_status": resp.status_code,
        }
    try:
        raw = resp.json()
    except ValueError:
        return {"ok": False, "error": "bad_response", "detail": "Unexpected response from Supabase."}
    ref = str((raw or {}).get("id") or (raw or {}).get("ref") or "").strip()
    return {
        "ok": True,
        "ref": ref,
        "name": str((raw or {}).get("name") or name),
        "url": _project_url(ref),
        "status": str((raw or {}).get("status") or ""),
    }

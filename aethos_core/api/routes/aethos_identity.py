# SPDX-License-Identifier: Apache-2.0
"""AethOS identity — contract runtime API plus enterprise authentication (§2).

This module hosts the real end-user auth layer:
  * Server-side sessions with secure, httpOnly, SameSite cookies (idle +
    absolute timeout, server-side store).
  * Local accounts with scrypt password hashing (memory-hard KDF from the
    already-vendored ``cryptography`` lib — no new dependency) and per-account
    brute-force lockout.
  * MFA/TOTP (RFC 6238, stdlib only) behind ``MFA_ENABLED``.
  * SSO via OIDC authorization-code + PKCE (back-channel exchange) behind
    ``SSO_ENABLED`` — works with Okta / Microsoft Entra / Google Workspace.
  * An ASGI middleware that enforces a valid session on protected routes when
    ``AUTH_ENABLED`` is set (default off → existing single-operator deploys are
    unchanged).

Secrets (session signing key, TOTP secrets) live under the data dir with 0600
perms, never in env. The store is a small JSON file guarded by a process lock;
that matches AethOS's existing file-backed stores and is sufficient for the
single-node / small-team scale this product targets.
"""

from __future__ import annotations

import base64
import hashlib
import hmac
import json
import os
import secrets
import struct
import threading
import time
from pathlib import Path
from typing import Any
from urllib.parse import urlencode

from fastapi import APIRouter, Request, Response
from pydantic import BaseModel, Field
from starlette.responses import JSONResponse

router = APIRouter(tags=["aethos-identity"])


def _audit(action: str, **kwargs: Any) -> None:
    """Best-effort write to the §3 unified audit ledger (never blocks auth)."""
    try:
        from aethos_core.observability.audit_ledger import record_audit_event

        record_audit_event(action=action, **kwargs)
    except Exception:  # noqa: BLE001 — auditing must never break the auth path
        pass


# ───────────────────────────── identity contract ──────────────────────────────


@router.get("/aethos-identity/status")
def identity_contract_status_api() -> dict[str, Any]:
    from aethos_core.aethos_identity.identity_contract_loader import get_identity_contract_status

    return get_identity_contract_status()


@router.post("/aethos-identity/reload")
def identity_contract_reload_api() -> dict[str, Any]:
    from aethos_core.aethos_identity.identity_contract_loader import reload_identity_contracts

    return reload_identity_contracts()


# ─────────────────────────────── storage layer ────────────────────────────────


def _auth_root() -> Path:
    from aethos_core.config import get_settings

    raw = Path(get_settings().auth_store_dir)
    if not raw.is_absolute():
        raw = Path(__file__).resolve().parents[3] / raw
    raw.mkdir(parents=True, exist_ok=True)
    try:
        os.chmod(raw, 0o700)
    except OSError:
        pass
    return raw


def _store_path() -> Path:
    return _auth_root() / "auth_store.json"


def _session_key() -> bytes:
    """Server session-signing key — generated once, stored 0600 under data."""
    path = _auth_root() / ".session_key"
    if path.exists():
        return path.read_bytes()
    key = secrets.token_bytes(32)
    path.write_bytes(key)
    try:
        os.chmod(path, 0o600)
    except OSError:
        pass
    return key


_LOCK = threading.RLock()


def _migrate_tenant_primary_user_roles(store: dict[str, Any]) -> bool:
    """One-time doctor upgrade: primary tenant users ``operator`` → ``tenant_admin``."""
    from aethos_core.config import get_settings
    from aethos_core.tenancy import DEFAULT_TENANT, normalize_tenant

    users = store.get("users") or {}
    if not users:
        return False
    multi = get_settings().multi_tenant_enabled
    changed = False
    for key, user in users.items():
        if not isinstance(user, dict):
            continue
        roles = list(user.get("roles") or [])
        uid = str(user.get("user_id") or user.get("email") or key).strip().lower()
        if not uid:
            continue
        tenant = normalize_tenant(uid) if multi else DEFAULT_TENANT
        is_primary = multi and tenant == uid
        if not multi and tenant == DEFAULT_TENANT and len(users) == 1:
            is_primary = True
        if not is_primary:
            continue
        if roles == ["operator"]:
            user["roles"] = ["tenant_admin"]
            changed = True
        elif "operator" in roles and "tenant_admin" not in roles and "admin" not in roles:
            user["roles"] = ["tenant_admin"] + [r for r in roles if r != "operator"]
            changed = True
    return changed


# Durable identity store. On any deployment with a database (DATABASE_URL /
# POSTGRES_URL — i.e. hosted on Railway, sharing Postgres-Zbbi with the vault) the
# whole identity document is persisted to the shared tenant_records table so it
# survives independently of the container/volume and matches how credentials are
# stored. Pure-local dev (no database) keeps the legacy 0600 JSON file unchanged.
# The document is global (all users), so it is keyed under the DEFAULT tenant.
_AUTH_STORE_NS = "auth_identity_store"
_AUTH_STORE_KEY = "global"


def _use_shared_store() -> bool:
    return bool(os.environ.get("DATABASE_URL") or os.environ.get("POSTGRES_URL"))


def _empty_store() -> dict[str, Any]:
    return {"users": {}, "sessions": {}, "oidc_flows": {}}


def _read_legacy_json_store() -> dict[str, Any] | None:
    """Read the on-disk JSON store if present (for one-time migration / local mode)."""
    path = _store_path()
    if not path.exists():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return None


def _load_store() -> dict[str, Any]:
    if _use_shared_store():
        from aethos_core.tenancy import DEFAULT_TENANT
        from aethos_core.tenancy.tenant_data_store import get_record

        data = get_record(_AUTH_STORE_NS, _AUTH_STORE_KEY, tenant_id=DEFAULT_TENANT, default=None)
        adopt_legacy = False
        if not isinstance(data, dict):
            # First run on the shared store: adopt the legacy JSON file (e.g. the
            # existing volume-backed store) so no users/sessions are lost.
            legacy = _read_legacy_json_store()
            data = legacy if isinstance(legacy, dict) else _empty_store()
            adopt_legacy = legacy is not None
        data.setdefault("users", {})
        data.setdefault("sessions", {})
        data.setdefault("oidc_flows", {})
        if adopt_legacy or _migrate_tenant_primary_user_roles(data):
            _save_store(data)
        return data

    data = _read_legacy_json_store()
    if not isinstance(data, dict):
        return _empty_store()
    data.setdefault("users", {})
    data.setdefault("sessions", {})
    data.setdefault("oidc_flows", {})
    if _migrate_tenant_primary_user_roles(data):
        _save_store(data)
    return data


def _save_store(store: dict[str, Any]) -> None:
    if _use_shared_store():
        from aethos_core.tenancy import DEFAULT_TENANT
        from aethos_core.tenancy.tenant_data_store import set_record

        set_record(_AUTH_STORE_NS, _AUTH_STORE_KEY, store, tenant_id=DEFAULT_TENANT)
        return

    path = _store_path()
    tmp = path.with_suffix(".tmp")
    tmp.write_text(json.dumps(store, indent=2, sort_keys=True), encoding="utf-8")
    os.replace(tmp, path)
    try:
        os.chmod(path, 0o600)
    except OSError:
        pass


# ──────────────────────────── password hashing ────────────────────────────────


def hash_password(password: str) -> str:
    """scrypt(N=2**15, r=8, p=1) — memory-hard, via cryptography (a hard dep)."""
    from cryptography.hazmat.primitives.kdf.scrypt import Scrypt

    salt = os.urandom(16)
    n, r, p = 2**15, 8, 1
    dk = Scrypt(salt=salt, length=32, n=n, r=r, p=p).derive(password.encode("utf-8"))
    b64 = base64.b64encode
    return f"scrypt${n}${r}${p}${b64(salt).decode()}${b64(dk).decode()}"


def verify_password(password: str, stored: str) -> bool:
    from cryptography.exceptions import InvalidKey
    from cryptography.hazmat.primitives.kdf.scrypt import Scrypt

    try:
        scheme, n_s, r_s, p_s, salt_b64, dk_b64 = stored.split("$")
        if scheme != "scrypt":
            return False
        salt = base64.b64decode(salt_b64)
        expected = base64.b64decode(dk_b64)
        Scrypt(salt=salt, length=len(expected), n=int(n_s), r=int(r_s), p=int(p_s)).verify(
            password.encode("utf-8"), expected
        )
        return True
    except (ValueError, InvalidKey):
        return False


# ──────────────────────────────── TOTP (MFA) ──────────────────────────────────


def new_totp_secret() -> str:
    return base64.b32encode(os.urandom(20)).decode("ascii").rstrip("=")


def _totp_at(secret_b32: str, counter: int, digits: int = 6) -> str:
    pad = "=" * (-len(secret_b32) % 8)
    key = base64.b32decode(secret_b32.upper() + pad, casefold=True)
    digest = hmac.new(key, struct.pack(">Q", counter), hashlib.sha1).digest()
    offset = digest[-1] & 0x0F
    code = struct.unpack(">I", digest[offset : offset + 4])[0] & 0x7FFFFFFF
    return str(code % (10**digits)).zfill(digits)


def verify_totp(secret_b32: str, code: str, *, step: int = 30, window: int = 1) -> bool:
    code = (code or "").strip().replace(" ", "")
    if not code.isdigit():
        return False
    counter = int(time.time() // step)
    for drift in range(-window, window + 1):
        if hmac.compare_digest(_totp_at(secret_b32, counter + drift), code):
            return True
    return False


def totp_provisioning_uri(secret_b32: str, account: str) -> str:
    from aethos_core.config import get_settings

    issuer = get_settings().mfa_issuer_label or "AethOS"
    label = urlencode({"secret": secret_b32, "issuer": issuer})
    return f"otpauth://totp/{issuer}:{account}?{label}"


# ─────────────────────────────── session model ────────────────────────────────


def _sign(session_id: str) -> str:
    mac = hmac.new(_session_key(), session_id.encode(), hashlib.sha256).hexdigest()
    return f"{session_id}.{mac}"


def _unsign(token: str) -> str | None:
    if not token or "." not in token:
        return None
    session_id, mac = token.rsplit(".", 1)
    expected = hmac.new(_session_key(), session_id.encode(), hashlib.sha256).hexdigest()
    if hmac.compare_digest(mac, expected):
        return session_id
    return None


def _create_session(store: dict[str, Any], user_id: str, *, method: str) -> str:
    from aethos_core.config import get_settings

    s = get_settings()
    now = time.time()
    session_id = secrets.token_urlsafe(32)
    store["sessions"][session_id] = {
        "user_id": user_id,
        "method": method,
        "created_at": now,
        "last_seen": now,
        "absolute_expiry": now + s.auth_session_absolute_timeout_sec,
        "idle_timeout": s.auth_session_idle_timeout_sec,
    }
    return session_id


def _validate_session(store: dict[str, Any], session_id: str) -> dict[str, Any] | None:
    sess = store["sessions"].get(session_id)
    if not sess:
        return None
    now = time.time()
    if now > sess.get("absolute_expiry", 0) or (now - sess.get("last_seen", 0)) > sess.get(
        "idle_timeout", 1800
    ):
        store["sessions"].pop(session_id, None)
        _save_store(store)
        return None
    sess["last_seen"] = now
    return sess


def _cookie_kwargs() -> dict[str, Any]:
    from aethos_core.config import get_settings

    s = get_settings()
    return {
        "httponly": True,
        "secure": bool(s.auth_cookie_secure),
        "samesite": "lax",
        "path": "/",
        "max_age": s.auth_session_absolute_timeout_sec,
    }


def _set_session_cookie(response: Response, session_id: str) -> None:
    from aethos_core.config import get_settings

    response.set_cookie(get_settings().auth_session_cookie, _sign(session_id), **_cookie_kwargs())


def _clear_session_cookie(response: Response) -> None:
    from aethos_core.config import get_settings

    response.delete_cookie(get_settings().auth_session_cookie, path="/")


# "pending" = re-registered after revoke/expiry; awaiting platform-owner approval.
_ENTITLEMENT_STATUSES = frozenset({"active", "trial", "expired", "revoked", "suspended", "pending"})

# Statuses a user can self-serve out of by re-registering (beta ended → come back).
_REACTIVATABLE_STATUSES = frozenset({"revoked", "suspended", "expired"})


def _normalize_entitlement(user: dict[str, Any]) -> dict[str, Any]:
    if "status" not in user:
        user["status"] = "trial"
    if "entitlement_source" not in user:
        user["entitlement_source"] = "manual"
    if "plan" not in user:
        user["plan"] = "beta"
    if "access_expires_at" not in user:
        user["access_expires_at"] = None
    return user


def _revoke_user_sessions(store: dict[str, Any], user_id: str) -> int:
    sessions = store.get("sessions") or {}
    killed = sum(1 for s in sessions.values() if s.get("user_id") == user_id)
    store["sessions"] = {
        sid: s for sid, s in sessions.items() if s.get("user_id") != user_id
    }
    return killed


def _entitlement_error_for_user(user: dict[str, Any]) -> str | None:
    from aethos_core.security.rbac import is_platform_owner

    if is_platform_owner(user):
        return None
    _normalize_entitlement(user)
    status = str(user.get("status") or "trial")
    if status == "pending":
        return "access_pending"
    if status in {"revoked", "suspended", "expired"}:
        return "access_revoked" if status == "revoked" else f"access_{status}"
    expires = user.get("access_expires_at")
    if expires is not None and float(expires) < time.time():
        user["status"] = "expired"
        return "access_expired"
    return None


def _entitlement_allows_access(user: dict[str, Any]) -> bool:
    return _entitlement_error_for_user(user) is None


def _session_from_request(request: Request) -> tuple[dict[str, Any], dict[str, Any]] | None:
    """Return (session, user) for the request's cookie, or None."""
    from aethos_core.config import get_settings

    token = request.cookies.get(get_settings().auth_session_cookie)
    if not token:
        return None
    session_id = _unsign(token)
    if not session_id:
        return None
    with _LOCK:
        store = _load_store()
        sess = _validate_session(store, session_id)
        if not sess:
            return None
        user = store["users"].get(sess["user_id"])
        if not user or user.get("disabled"):
            return None
        err = _entitlement_error_for_user(user)
        if err:
            _revoke_user_sessions(store, str(user.get("user_id") or ""))
            _save_store(store)
            request.state.entitlement_error = err
            return None
        _save_store(store)
        return sess, user


def current_user(request: Request) -> dict[str, Any] | None:
    found = _session_from_request(request)
    return found[1] if found else None


# ─────────────────────────────── middleware ───────────────────────────────────

# Paths that never require a session (auth endpoints, health, docs, root).
_OPEN_PREFIXES = (
    "/api/v1/aethos-identity/login",
    "/api/v1/aethos-identity/logout",
    "/api/v1/aethos-identity/register",
    "/api/v1/aethos-identity/session",
    "/api/v1/aethos-identity/bootstrap",
    "/api/v1/aethos-identity/verify-email",
    "/api/v1/aethos-identity/resend-verification",
    "/api/v1/aethos-identity/sso/",
    "/api/v1/aethos-identity/mfa/verify",
    "/api/v1/aethos-identity/billing/webhook",
    "/api/v1/aethos-identity/billing/stripe/webhook",
    "/api/v1/health",
    "/api/v1/version",
    "/version",
    # External channel webhooks — authenticated by provider signatures/secrets, not sessions.
    "/api/v1/channels/telegram/webhook",
    "/api/v1/channels/slack/events",
    "/api/v1/channels/discord/interactions",
    "/api/v1/channels/whatsapp/webhook",
    "/api/v1/channels/messenger/webhook",
)
_OPEN_EXACT = (
    "/",
    "/aethos",
    "/docs",
    "/redoc",
    "/openapi.json",
    "/favicon.ico",
    "/api/v1/external-execution/webhook/trigger",
)
# Public web UI routes that may hit the API host when email links or proxies mis-route.
_WEB_PUBLIC_PREFIXES = (
    "/verify-email",
    "/login",
    "/register",
    "/resend-verification",
    "/aethos/verify-email",
    "/aethos/login",
    "/aethos/register",
    "/aethos/resend-verification",
    "/_next/",
    "/aethos/_next/",
    "/manifest.webmanifest",
    "/aethos/manifest.webmanifest",
)


def _is_open_path(path: str, method: str = "GET") -> bool:
    if path in _OPEN_EXACT or path.startswith("/docs") or path.startswith("/redoc"):
        return True
    if any(path.startswith(p) for p in _OPEN_PREFIXES):
        return True
    if any(path.startswith(p) for p in _WEB_PUBLIC_PREFIXES):
        return True
    # Automation webhook fire uses X-AethOS-Webhook-Secret — not a session cookie.
    if (
        path.startswith("/api/v1/automation/webhooks/")
        and path != "/api/v1/automation/webhooks"
        and method.upper() != "GET"
    ):
        return True
    return False


async def auth_session_middleware(request: Request, call_next):
    """Enforce a valid session on protected routes when AUTH_ENABLED (§2).

    Multi-tenancy implies auth: when ``MULTI_TENANT_ENABLED`` is on, sessions are
    enforced even if ``AUTH_ENABLED`` was left off — a shared deployment must fail
    closed (anonymous requests cannot be attributed to a tenant).
    """
    from starlette.responses import JSONResponse

    from aethos_core.config import get_settings

    s = get_settings()
    enforce = bool(s.auth_enabled) or bool(s.multi_tenant_enabled)
    if not enforce or request.method == "OPTIONS" or _is_open_path(request.url.path, request.method):
        return await call_next(request)

    found = _session_from_request(request)
    if not found:
        entitlement_error = getattr(request.state, "entitlement_error", None)
        if entitlement_error:
            response = JSONResponse({"error": entitlement_error}, status_code=403)
            _clear_session_cookie(response)
            return response
        return JSONResponse({"error": "authentication_required"}, status_code=401)
    sess, user = found
    request.state.user = user
    request.state.session = sess
    return await call_next(request)


# ──────────────────────────── user helpers ────────────────────────────────────


def _domain_allowed(email: str) -> bool:
    from aethos_core.config import get_settings

    allowed = [d.strip().lower() for d in get_settings().oidc_allowed_domains.split(",") if d.strip()]
    if not allowed:
        return True
    return email.split("@")[-1].lower() in allowed


def _upsert_sso_user(store: dict[str, Any], email: str, name: str) -> str:
    user_id = email.lower()
    user = store["users"].get(user_id) or {
        "user_id": user_id,
        "email": email,
        "name": name,
        "roles": ["tenant_admin"],
        "auth": "sso",
        "created_at": time.time(),
        "status": "trial",
        "entitlement_source": "manual",
        "plan": "beta",
        "access_expires_at": None,
    }
    _normalize_entitlement(user)
    user["last_login"] = time.time()
    user["name"] = name or user.get("name", "")
    store["users"][user_id] = user
    return user_id


# ──────────────────────────────── schemas ─────────────────────────────────────


class BootstrapIn(BaseModel):
    email: str
    password: str


class LoginIn(BaseModel):
    email: str
    password: str
    totp: str | None = None


class RegisterIn(BaseModel):
    email: str
    password: str
    name: str | None = None


class MfaVerifyIn(BaseModel):
    email: str
    totp: str


# ──────────────────────────── local auth endpoints ────────────────────────────


@router.get("/aethos-identity/session")
def session_status_api(request: Request) -> dict[str, Any]:
    from starlette.responses import JSONResponse

    from aethos_core.config import get_settings

    s = get_settings()
    found = _session_from_request(request)
    entitlement_error = getattr(request.state, "entitlement_error", None)
    if entitlement_error:
        response = JSONResponse(
            {
                "auth_enabled": bool(s.auth_enabled),
                "authenticated": False,
                "error": entitlement_error,
            },
            status_code=403,
        )
        _clear_session_cookie(response)
        return response
    base = {
        "auth_enabled": bool(s.auth_enabled),
        "sso_enabled": bool(s.sso_enabled),
        "mfa_enabled": bool(s.mfa_enabled),
        "self_signup_enabled": bool(s.auth_self_signup_enabled),
        "multi_tenant_enabled": bool(s.multi_tenant_enabled),
    }
    if not found:
        return {**base, "authenticated": False}
    _, user = found
    from aethos_core.auth.email_verification import email_verification_required, user_email_verified
    from aethos_core.security.rbac import is_platform_owner, is_tenant_owner, permissions_for_user

    _normalize_entitlement(user)
    return {
        **base,
        "authenticated": True,
        "is_platform_owner": is_platform_owner(user),
        "is_tenant_owner": is_tenant_owner(user),
        "email_verification_required": email_verification_required(),
        "email_verified": user_email_verified(user),
        "user": {
            "email": user.get("email"),
            "name": user.get("name"),
            "roles": user.get("roles", []),
            "permissions": sorted(permissions_for_user(user)),
            "mfa_enrolled": bool(user.get("totp_secret")),
            "email_verified": user_email_verified(user),
            "status": user.get("status"),
            "plan": user.get("plan"),
            "access_expires_at": user.get("access_expires_at"),
        },
    }


@router.post("/aethos-identity/bootstrap")
def bootstrap_admin_api(body: BootstrapIn) -> dict[str, Any]:
    """Create the first admin account. Only allowed when no users exist, and the
    email must match AUTH_BOOTSTRAP_ADMIN_EMAIL if that is configured."""
    from aethos_core.config import get_settings

    s = get_settings()
    with _LOCK:
        store = _load_store()
        if store["users"]:
            return {"ok": False, "error": "already_bootstrapped"}
        configured = s.auth_bootstrap_admin_email.strip().lower()
        if configured and body.email.strip().lower() != configured:
            return {"ok": False, "error": "email_not_allowed"}
        if len(body.password) < 12:
            return {"ok": False, "error": "weak_password", "detail": "min 12 chars"}
        user_id = body.email.strip().lower()
        store["users"][user_id] = {
            "user_id": user_id,
            "email": body.email.strip(),
            "name": "Administrator",
            "roles": ["admin", "approver", "operator"],
            "auth": "local",
            "password": hash_password(body.password),
            "created_at": time.time(),
            "status": "active",
            "entitlement_source": "manual",
            "plan": "admin",
            "access_expires_at": None,
        }
        _save_store(store)
    return {"ok": True, "user_id": user_id, "roles": ["admin", "approver", "operator"]}


def _locked_out(user: dict[str, Any]) -> bool:
    from aethos_core.config import get_settings

    s = get_settings()
    fails = user.get("failed_logins", 0)
    last = user.get("last_failed", 0)
    if fails >= s.auth_login_max_attempts and (time.time() - last) < s.auth_login_lockout_sec:
        return True
    return False


@router.post("/aethos-identity/login")
def login_api(body: LoginIn, response: Response) -> dict[str, Any]:
    from aethos_core.config import get_settings

    s = get_settings()
    user_id = body.email.strip().lower()
    with _LOCK:
        store = _load_store()
        user = store["users"].get(user_id)
        # Constant-ish work even when the user is missing (mitigate enumeration).
        if not user or user.get("auth") != "local":
            hash_password("dummy-work-factor")
            return {"ok": False, "error": "invalid_credentials"}
        if user.get("disabled"):
            return {"ok": False, "error": "account_disabled"}
        if not _entitlement_allows_access(user):
            err = _entitlement_error_for_user(user) or "access_revoked"
            return {"ok": False, "error": err}
        if _locked_out(user):
            return {"ok": False, "error": "account_locked", "retry_after_sec": s.auth_login_lockout_sec}
        if not verify_password(body.password, user.get("password", "")):
            user["failed_logins"] = user.get("failed_logins", 0) + 1
            user["last_failed"] = time.time()
            _save_store(store)
            _audit("auth.login_failed", actor=user_id, outcome="denied")
            return {"ok": False, "error": "invalid_credentials"}
        from aethos_core.auth.email_verification import email_verification_required, user_email_verified

        if email_verification_required() and not user_email_verified(user):
            return {"ok": False, "error": "email_verification_required"}
        # Password OK → MFA gate.
        if s.mfa_enabled and user.get("totp_secret"):
            if not body.totp:
                return {"ok": False, "error": "mfa_required", "mfa": True}
            if not verify_totp(user["totp_secret"], body.totp):
                user["failed_logins"] = user.get("failed_logins", 0) + 1
                user["last_failed"] = time.time()
                _save_store(store)
                return {"ok": False, "error": "invalid_mfa"}
        elif s.mfa_enabled and s.mfa_required and not user.get("totp_secret"):
            return {"ok": False, "error": "mfa_enrollment_required", "enroll": True}
        user["failed_logins"] = 0
        user["last_login"] = time.time()
        session_id = _create_session(store, user_id, method="password")
        _save_store(store)
    _set_session_cookie(response, session_id)
    _audit("auth.login", actor=user_id, metadata={"method": "password"})
    return {"ok": True, "user": {"email": user["email"], "roles": user.get("roles", [])}}


def _issue_verification_email(request: Request, user: dict[str, Any]) -> dict[str, Any]:
    from aethos_core.auth.email_verification import (
        build_verification_url,
        compose_verification_email,
        new_verification_token,
    )
    from aethos_core.auth.transactional_email import send_transactional_email

    token, expires = new_verification_token()
    user["verification_token"] = token
    user["verification_expires"] = expires
    user["email_verified"] = False
    user["verification_sent_at"] = time.time()
    verify_url = build_verification_url(request, token)
    subject, body = compose_verification_email(
        verify_url=verify_url,
        name=str(user.get("name") or ""),
    )
    sent = send_transactional_email(str(user.get("email") or ""), subject, body)
    return sent


@router.post("/aethos-identity/register")
def register_api(body: RegisterIn, request: Request, response: Response) -> dict[str, Any]:
    """Self-service signup for local email+password accounts (beta onboarding)."""
    from aethos_core.auth.email_verification import email_verification_required
    from aethos_core.auth.transactional_email import transactional_mailer_configured
    from aethos_core.config import get_settings

    s = get_settings()
    if not s.auth_self_signup_enabled:
        return {"ok": False, "error": "signup_disabled"}

    email = body.email.strip()
    user_id = email.lower()
    if "@" not in user_id or "." not in user_id.split("@")[-1]:
        return {"ok": False, "error": "invalid_email"}
    if len(body.password) < 12:
        return {"ok": False, "error": "weak_password", "detail": "min 12 chars"}
    if not any(c.isalpha() for c in body.password) or not any(c.isdigit() for c in body.password):
        return {
            "ok": False,
            "error": "weak_password",
            "detail": "Use at least 12 characters with letters and numbers.",
        }

    verify_required = email_verification_required()
    if verify_required and not transactional_mailer_configured():
        return {
            "ok": False,
            "error": "mailer_not_configured",
            "detail": "Email verification is required on hosted deploys. Configure RESEND_API_KEY, "
            "SendGrid, or SMTP (EMAIL_FROM + SMTP_HOST) before enabling public signup.",
        }

    with _LOCK:
        store = _load_store()
        existing = store["users"].get(user_id)
        if existing:
            _normalize_entitlement(existing)
            existing_status = str(existing.get("status") or "trial")
            # In good standing → genuinely taken; send them to sign-in.
            if existing_status not in _REACTIVATABLE_STATUSES:
                return {"ok": False, "error": "email_taken"}
            # Beta ended / revoked → allow re-registration as a REACTIVATION that lands
            # in "pending" until the platform owner grants access (the "re-register for
            # the paid version" path). Email verification gates it, so only the inbox
            # owner can complete it — no takeover. No session is created here.
            existing["password"] = hash_password(body.password)
            existing["name"] = (body.name or "").strip() or existing.get("name") or email.split("@")[0]
            existing["status"] = "pending"
            existing["entitlement_source"] = "self_reregister"
            existing["access_expires_at"] = None
            existing["failed_logins"] = 0
            if verify_required:
                sent = _issue_verification_email(request, existing)
                if not sent.get("ok"):
                    out: dict[str, Any] = {
                        "ok": False,
                        "error": "verification_email_failed",
                        "detail": sent.get("detail") or "Could not send verification email.",
                    }
                    if sent.get("hint"):
                        out["hint"] = sent.get("hint")
                    return out
            else:
                existing["email_verified"] = True
            _save_store(store)
            _audit("auth.reregister_pending", actor=user_id, metadata={"from_status": existing_status})
            return {
                "ok": True,
                "pending": True,
                "verification_required": verify_required,
                "detail": (
                    "Your previous access ended. We've re-registered you — verify your email, then your "
                    "account is pending approval before you can sign in."
                    if verify_required
                    else "Your previous access ended. Re-registered — your account is pending approval before sign-in."
                ),
            }
        user_row: dict[str, Any] = {
            "user_id": user_id,
            "email": email,
            "name": (body.name or "").strip() or email.split("@")[0],
            "roles": ["tenant_admin"],
            "auth": "local",
            "password": hash_password(body.password),
            "created_at": time.time(),
            "email_verified": not verify_required,
            "status": "trial",
            "entitlement_source": "manual",
            "plan": "beta",
            "access_expires_at": None,
        }
        store["users"][user_id] = user_row
        session_id: str | None = None
        if verify_required:
            sent = _issue_verification_email(request, user_row)
            if not sent.get("ok"):
                del store["users"][user_id]
                out: dict[str, Any] = {
                    "ok": False,
                    "error": "verification_email_failed",
                    "detail": sent.get("detail") or "Could not send verification email.",
                }
                if sent.get("hint"):
                    out["hint"] = sent.get("hint")
                if sent.get("provider"):
                    out["provider"] = sent.get("provider")
                if sent.get("status") is not None:
                    out["status"] = sent.get("status")
                return out
        elif not (s.mfa_enabled and s.mfa_required):
            user_row["last_login"] = time.time()
            session_id = _create_session(store, user_id, method="password")
        _save_store(store)

    _audit("auth.register", actor=user_id, metadata={"method": "self_signup", "verified": not verify_required})
    if session_id:
        _set_session_cookie(response, session_id)
        return {"ok": True, "user": {"email": email, "roles": ["tenant_admin"]}}
    if verify_required:
        return {
            "ok": True,
            "verification_required": True,
            "user": {"email": email, "roles": ["tenant_admin"]},
        }
    return {"ok": True, "user": {"email": email, "roles": ["tenant_admin"]}, "mfa_enrollment_required": True}


class ResendVerificationIn(BaseModel):
    email: str


@router.get("/aethos-identity/verify-email")
def verify_email_api(token: str = "") -> dict[str, Any]:
    tok = (token or "").strip()
    if not tok:
        return {"ok": False, "error": "token_required"}
    with _LOCK:
        store = _load_store()
        for user_id, user in store["users"].items():
            if str(user.get("verification_token") or "") != tok:
                continue
            if float(user.get("verification_expires") or 0) < time.time():
                return {"ok": False, "error": "token_expired"}
            user["email_verified"] = True
            user.pop("verification_token", None)
            user.pop("verification_expires", None)
            _save_store(store)
            _audit("auth.email_verified", actor=user_id)
            return {"ok": True, "email": user.get("email")}
    return {"ok": False, "error": "invalid_token"}


@router.post("/aethos-identity/resend-verification")
def resend_verification_api(body: ResendVerificationIn, request: Request) -> dict[str, Any]:
    from aethos_core.auth.email_verification import email_verification_required, user_email_verified
    from aethos_core.config import get_settings

    if not email_verification_required():
        return {"ok": False, "error": "verification_not_required"}
    user_id = body.email.strip().lower()
    if not user_id:
        return {"ok": False, "error": "invalid_email"}
    s = get_settings()
    with _LOCK:
        store = _load_store()
        user = store["users"].get(user_id)
        if not user or user.get("auth") != "local":
            return {"ok": True}
        if user_email_verified(user):
            return {"ok": True, "already_verified": True}
        last = float(user.get("verification_sent_at") or 0)
        if last and (time.time() - last) < s.auth_verification_resend_cooldown_sec:
            return {
                "ok": False,
                "error": "resend_cooldown",
                "retry_after_sec": int(s.auth_verification_resend_cooldown_sec - (time.time() - last)),
            }
        sent = _issue_verification_email(request, user)
        if not sent.get("ok"):
            out = {
                "ok": False,
                "error": "verification_email_failed",
                "detail": sent.get("detail"),
            }
            if sent.get("hint"):
                out["hint"] = sent.get("hint")
            if sent.get("provider"):
                out["provider"] = sent.get("provider")
            if sent.get("status") is not None:
                out["status"] = sent.get("status")
            return out
        _save_store(store)
    return {"ok": True}


class MailerTestIn(BaseModel):
    to: str = Field(min_length=3, max_length=200)


def _require_mailer_test_actor(request: Request) -> dict[str, Any] | None:
    from aethos_core.config import get_settings

    if not get_settings().auth_enabled and not get_settings().multi_tenant_enabled:
        return {"email": "local-operator", "roles": ["admin", "operator"]}
    found = _session_from_request(request)
    if not found:
        return None
    _, user = found
    roles = set(user.get("roles") or [])
    if "admin" in roles or "operator" in roles:
        return user
    return None


@router.post("/aethos-identity/mailer-test")
def mailer_test_api(body: MailerTestIn, request: Request) -> dict[str, Any]:
    """Send a diagnostic email and return the full provider result (redacted)."""
    actor = _require_mailer_test_actor(request)
    if actor is None:
        return {"ok": False, "error": "forbidden"}
    from aethos_core.auth.transactional_email import send_mailer_test_email

    to_addr = body.to.strip()
    if "@" not in to_addr:
        return {"ok": False, "error": "invalid_email"}
    result = send_mailer_test_email(to_addr)
    _audit("auth.mailer_test", actor=actor.get("user_id") or actor.get("email"), metadata={"to": to_addr, "ok": result.get("ok")})
    return {"ok": bool(result.get("ok")), **{k: v for k, v in result.items() if k != "ok"}}


@router.post("/aethos-identity/logout")
def logout_api(request: Request, response: Response) -> dict[str, Any]:
    from aethos_core.config import get_settings

    token = request.cookies.get(get_settings().auth_session_cookie)
    if token:
        session_id = _unsign(token)
        if session_id:
            with _LOCK:
                store = _load_store()
                popped = store["sessions"].pop(session_id, None)
                if popped is not None:
                    _save_store(store)
                    _audit("auth.logout", actor=popped.get("user_id"))
    _clear_session_cookie(response)
    return {"ok": True}


@router.post("/aethos-identity/mfa/enroll")
def mfa_enroll_api(request: Request) -> dict[str, Any]:
    """Generate (but don't yet activate) a TOTP secret for the current user."""
    from aethos_core.config import get_settings

    if not get_settings().mfa_enabled:
        return {"ok": False, "error": "mfa_disabled"}
    found = _session_from_request(request)
    if not found:
        return {"ok": False, "error": "authentication_required"}
    _, user = found
    secret = new_totp_secret()
    with _LOCK:
        store = _load_store()
        store["users"][user["user_id"]]["totp_pending"] = secret
        _save_store(store)
    return {
        "ok": True,
        "secret": secret,
        "otpauth_uri": totp_provisioning_uri(secret, user["email"]),
    }


@router.post("/aethos-identity/mfa/verify")
def mfa_verify_api(body: MfaVerifyIn) -> dict[str, Any]:
    """Activate a pending TOTP enrollment by confirming a live code."""
    user_id = body.email.strip().lower()
    with _LOCK:
        store = _load_store()
        user = store["users"].get(user_id)
        if not user or not user.get("totp_pending"):
            return {"ok": False, "error": "no_pending_enrollment"}
        if not verify_totp(user["totp_pending"], body.totp):
            return {"ok": False, "error": "invalid_mfa"}
        user["totp_secret"] = user.pop("totp_pending")
        _save_store(store)
    return {"ok": True, "mfa_enrolled": True}


# ──────────────────────────────── SSO (OIDC) ──────────────────────────────────


def _oidc_discovery() -> dict[str, Any]:
    import httpx

    from aethos_core.config import get_settings

    issuer = get_settings().oidc_issuer.rstrip("/")
    url = f"{issuer}/.well-known/openid-configuration"
    with httpx.Client(timeout=10.0) as client:
        resp = client.get(url)
        resp.raise_for_status()
        return resp.json()


def _pkce_pair() -> tuple[str, str]:
    verifier = secrets.token_urlsafe(64)
    challenge = base64.urlsafe_b64encode(
        hashlib.sha256(verifier.encode()).digest()
    ).decode().rstrip("=")
    return verifier, challenge


@router.get("/aethos-identity/sso/login")
def sso_login_api(response: Response) -> dict[str, Any]:
    from aethos_core.config import get_settings

    s = get_settings()
    if not s.sso_enabled:
        return {"ok": False, "error": "sso_disabled"}
    if not (s.oidc_issuer and s.oidc_client_id and s.oidc_redirect_url):
        return {"ok": False, "error": "sso_misconfigured"}
    try:
        disco = _oidc_discovery()
    except Exception:  # noqa: BLE001 — network/IdP errors surface as a clean failure
        return {"ok": False, "error": "oidc_discovery_failed"}
    state = secrets.token_urlsafe(24)
    nonce = secrets.token_urlsafe(24)
    verifier, challenge = _pkce_pair()
    with _LOCK:
        store = _load_store()
        store["oidc_flows"][state] = {
            "nonce": nonce,
            "verifier": verifier,
            "created_at": time.time(),
        }
        # Drop flows older than 10 min.
        store["oidc_flows"] = {
            k: v for k, v in store["oidc_flows"].items() if time.time() - v["created_at"] < 600
        }
        _save_store(store)
    params = {
        "response_type": "code",
        "client_id": s.oidc_client_id,
        "redirect_uri": s.oidc_redirect_url,
        "scope": s.oidc_scopes,
        "state": state,
        "nonce": nonce,
        "code_challenge": challenge,
        "code_challenge_method": "S256",
    }
    return {"ok": True, "authorize_url": f"{disco['authorization_endpoint']}?{urlencode(params)}"}


@router.get("/aethos-identity/sso/callback")
def sso_callback_api(request: Request, response: Response, code: str = "", state: str = "") -> Any:
    import httpx
    from starlette.responses import RedirectResponse

    from aethos_core.config import get_settings

    s = get_settings()
    if not s.sso_enabled:
        return {"ok": False, "error": "sso_disabled"}
    with _LOCK:
        store = _load_store()
        flow = store["oidc_flows"].pop(state, None)
        _save_store(store)
    if not flow or not code:
        return {"ok": False, "error": "invalid_state"}
    try:
        disco = _oidc_discovery()
        with httpx.Client(timeout=10.0) as client:
            token_resp = client.post(
                disco["token_endpoint"],
                data={
                    "grant_type": "authorization_code",
                    "code": code,
                    "redirect_uri": s.oidc_redirect_url,
                    "client_id": s.oidc_client_id,
                    "client_secret": s.oidc_client_secret,
                    "code_verifier": flow["verifier"],
                },
            )
            token_resp.raise_for_status()
            tokens = token_resp.json()
            # Back-channel userinfo with the freshly-minted access token (the code
            # exchange itself is the trust anchor: server↔IdP over TLS w/ secret).
            userinfo_resp = client.get(
                disco["userinfo_endpoint"],
                headers={"Authorization": f"Bearer {tokens['access_token']}"},
            )
            userinfo_resp.raise_for_status()
            userinfo = userinfo_resp.json()
    except Exception:  # noqa: BLE001
        return {"ok": False, "error": "oidc_exchange_failed"}

    email = (userinfo.get("email") or "").strip()
    if not email or (userinfo.get("email_verified") is False) or not _domain_allowed(email):
        return {"ok": False, "error": "email_not_allowed"}
    name = userinfo.get("name") or userinfo.get("preferred_username") or email
    with _LOCK:
        store = _load_store()
        user_id = _upsert_sso_user(store, email, name)
        session_id = _create_session(store, user_id, method="sso")
        _save_store(store)
    _audit("auth.sso_login", actor=user_id, metadata={"method": "oidc"})
    _set_session_cookie(response, session_id)
    # Land the browser back on the app root with the cookie set.
    redirect = RedirectResponse(url="/", status_code=303)
    _set_session_cookie(redirect, session_id)
    return redirect


# ──────────────────────── §7 user/role administration ─────────────────────────


class RoleUpdateIn(BaseModel):
    email: str
    roles: list[str]


class UserStateIn(BaseModel):
    email: str
    disabled: bool = True


def _require_manage_users(request: Request) -> dict[str, Any] | None:
    """Return the acting admin user, or None if not permitted. When auth is off,
    the local single operator is trusted (returns a synthetic admin)."""
    from aethos_core.config import get_settings
    from aethos_core.security.rbac import MANAGE_USERS, permissions_for_user

    if not get_settings().auth_enabled:
        return {"email": "local-operator", "roles": ["admin"]}
    found = _session_from_request(request)
    if not found:
        return None
    _, user = found
    if MANAGE_USERS not in permissions_for_user(user):
        return None
    return user


@router.get("/aethos-identity/users")
def list_users_api(request: Request) -> dict[str, Any]:
    if _require_manage_users(request) is None:
        return {"ok": False, "error": "forbidden"}
    with _LOCK:
        store = _load_store()
        users = [
            {
                "email": u.get("email"),
                "name": u.get("name"),
                "roles": u.get("roles", []),
                "auth": u.get("auth"),
                "disabled": bool(u.get("disabled")),
                "mfa_enrolled": bool(u.get("totp_secret")),
                "last_login": u.get("last_login"),
                "status": _normalize_entitlement(dict(u)).get("status"),
                "plan": u.get("plan"),
                "access_expires_at": u.get("access_expires_at"),
                "entitlement_source": u.get("entitlement_source"),
            }
            for u in store["users"].values()
        ]
    from aethos_core.security.rbac import VALID_ROLES

    return {"ok": True, "users": users, "valid_roles": list(VALID_ROLES)}


@router.post("/aethos-identity/users/roles")
def set_user_roles_api(body: RoleUpdateIn, request: Request) -> dict[str, Any]:
    actor = _require_manage_users(request)
    if actor is None:
        return {"ok": False, "error": "forbidden"}
    from aethos_core.security.rbac import VALID_ROLES

    roles = [r for r in body.roles if r in VALID_ROLES]
    if not roles:
        return {"ok": False, "error": "no_valid_roles", "valid_roles": list(VALID_ROLES)}
    user_id = body.email.strip().lower()
    with _LOCK:
        store = _load_store()
        user = store["users"].get(user_id)
        if not user:
            return {"ok": False, "error": "user_not_found"}
        # Don't allow removing the last admin.
        if "admin" not in roles and user.get("roles") and "admin" in user["roles"]:
            admins = [u for u in store["users"].values() if "admin" in u.get("roles", [])]
            if len(admins) <= 1:
                return {"ok": False, "error": "cannot_remove_last_admin"}
        user["roles"] = roles
        _save_store(store)
    _audit(
        "user.roles_changed",
        actor=actor.get("email"),
        target=user_id,
        after={"roles": roles},
    )
    return {"ok": True, "email": user_id, "roles": roles}


@router.post("/aethos-identity/users/state")
def set_user_state_api(body: UserStateIn, request: Request) -> dict[str, Any]:
    actor = _require_manage_users(request)
    if actor is None:
        return {"ok": False, "error": "forbidden"}
    user_id = body.email.strip().lower()
    with _LOCK:
        store = _load_store()
        user = store["users"].get(user_id)
        if not user:
            return {"ok": False, "error": "user_not_found"}
        if body.disabled and "admin" in user.get("roles", []):
            admins = [
                u
                for u in store["users"].values()
                if "admin" in u.get("roles", []) and not u.get("disabled")
            ]
            if len(admins) <= 1:
                return {"ok": False, "error": "cannot_disable_last_admin"}
        user["disabled"] = bool(body.disabled)
        # Revoke active sessions for a disabled user.
        if body.disabled:
            store["sessions"] = {
                sid: s for sid, s in store["sessions"].items() if s.get("user_id") != user_id
            }
        _save_store(store)
    return {"ok": True, "email": user_id, "disabled": bool(body.disabled)}


# ───────────────────── platform owner console (env-computed owner only) ───────


def _require_platform_owner(request: Request) -> dict[str, Any] | None:
    from aethos_core.security.rbac import is_platform_owner

    found = _session_from_request(request)
    if not found:
        return None
    _, user = found
    if not is_platform_owner(user):
        return None
    return user


def _user_session_count(store: dict[str, Any], user_id: str) -> int:
    return sum(1 for s in store.get("sessions", {}).values() if s.get("user_id") == user_id)


def _resolve_owner_user_id(store: dict[str, Any], user_ref: str) -> str | None:
    ref = (user_ref or "").strip().lower()
    if not ref:
        return None
    if ref in store.get("users", {}):
        return ref
    for uid, row in store.get("users", {}).items():
        if str(row.get("email") or "").lower() == ref:
            return uid
    return None


class OwnerGrantIn(BaseModel):
    status: str = "trial"
    plan: str = "beta"
    access_expires_at: float | None = None
    trial_days: int | None = Field(default=None, ge=1, le=3650)


class OwnerExtendIn(BaseModel):
    days: int = Field(default=30, ge=1, le=3650)


@router.get("/aethos-identity/admin/users")
def owner_list_users_api(request: Request) -> dict[str, Any]:
    if _require_platform_owner(request) is None:
        return {"ok": False, "error": "forbidden"}
    with _LOCK:
        store = _load_store()
        users = []
        for uid, u in store["users"].items():
            row = _normalize_entitlement(dict(u))
            users.append(
                {
                    "user_id": uid,
                    "email": row.get("email"),
                    "name": row.get("name"),
                    "status": row.get("status"),
                    "plan": row.get("plan"),
                    "access_expires_at": row.get("access_expires_at"),
                    "entitlement_source": row.get("entitlement_source"),
                    "roles": row.get("roles", []),
                    "disabled": bool(row.get("disabled")),
                    "last_login": row.get("last_login"),
                    "session_count": _user_session_count(store, uid),
                }
            )
    return {"ok": True, "users": users}


@router.post("/aethos-identity/admin/users/{user_ref}/grant")
def owner_grant_user_api(user_ref: str, body: OwnerGrantIn, request: Request) -> dict[str, Any]:
    actor = _require_platform_owner(request)
    if actor is None:
        return {"ok": False, "error": "forbidden"}
    status = (body.status or "trial").strip().lower()
    if status not in _ENTITLEMENT_STATUSES:
        return {"ok": False, "error": "invalid_status", "valid": sorted(_ENTITLEMENT_STATUSES)}
    with _LOCK:
        store = _load_store()
        user_id = _resolve_owner_user_id(store, user_ref)
        if not user_id:
            return {"ok": False, "error": "user_not_found"}
        user = store["users"][user_id]
        _normalize_entitlement(user)
        user["status"] = status
        user["plan"] = (body.plan or "beta").strip() or "beta"
        user["entitlement_source"] = "manual"
        if body.trial_days is not None:
            user["access_expires_at"] = time.time() + body.trial_days * 86400
        elif body.access_expires_at is not None:
            user["access_expires_at"] = float(body.access_expires_at)
        _save_store(store)
    _audit(
        "owner.grant_entitlement",
        actor=str(actor.get("email") or ""),
        target=user_id,
        after={
            "status": status,
            "plan": user.get("plan"),
            "access_expires_at": user.get("access_expires_at"),
        },
    )
    return {
        "ok": True,
        "user_id": user_id,
        "status": user.get("status"),
        "plan": user.get("plan"),
        "access_expires_at": user.get("access_expires_at"),
    }


@router.post("/aethos-identity/admin/users/{user_ref}/revoke")
def owner_revoke_user_api(user_ref: str, request: Request) -> dict[str, Any]:
    actor = _require_platform_owner(request)
    if actor is None:
        return {"ok": False, "error": "forbidden"}
    with _LOCK:
        store = _load_store()
        user_id = _resolve_owner_user_id(store, user_ref)
        if not user_id:
            return {"ok": False, "error": "user_not_found"}
        user = store["users"][user_id]
        from aethos_core.security.rbac import is_platform_owner

        if is_platform_owner(user):
            return {"ok": False, "error": "cannot_revoke_platform_owner"}
        user["status"] = "revoked"
        killed = _revoke_user_sessions(store, user_id)
        _save_store(store)
    _audit("owner.revoke_user", actor=str(actor.get("email") or ""), target=user_id, metadata={"sessions_killed": killed})
    return {"ok": True, "user_id": user_id, "status": "revoked", "sessions_killed": killed}


@router.post("/aethos-identity/admin/users/{user_ref}/extend")
def owner_extend_user_api(user_ref: str, body: OwnerExtendIn, request: Request) -> dict[str, Any]:
    actor = _require_platform_owner(request)
    if actor is None:
        return {"ok": False, "error": "forbidden"}
    with _LOCK:
        store = _load_store()
        user_id = _resolve_owner_user_id(store, user_ref)
        if not user_id:
            return {"ok": False, "error": "user_not_found"}
        user = store["users"][user_id]
        _normalize_entitlement(user)
        base = float(user.get("access_expires_at") or time.time())
        if base < time.time():
            base = time.time()
        user["access_expires_at"] = base + body.days * 86400
        if user.get("status") == "expired":
            user["status"] = "trial"
        _save_store(store)
    _audit(
        "owner.extend_entitlement",
        actor=str(actor.get("email") or ""),
        target=user_id,
        after={"access_expires_at": user.get("access_expires_at")},
    )
    return {"ok": True, "user_id": user_id, "access_expires_at": user.get("access_expires_at")}


@router.post("/aethos-identity/admin/users/{user_ref}/reinstate")
def owner_reinstate_user_api(user_ref: str, request: Request) -> dict[str, Any]:
    actor = _require_platform_owner(request)
    if actor is None:
        return {"ok": False, "error": "forbidden"}
    with _LOCK:
        store = _load_store()
        user_id = _resolve_owner_user_id(store, user_ref)
        if not user_id:
            return {"ok": False, "error": "user_not_found"}
        user = store["users"][user_id]
        _normalize_entitlement(user)
        user["status"] = "active"
        user["disabled"] = False
        _save_store(store)
    _audit("owner.reinstate_user", actor=str(actor.get("email") or ""), target=user_id)
    return {"ok": True, "user_id": user_id, "status": "active"}


# ───────────────────────────── billing seam (Stripe-ready) ────────────────────


class BillingWebhookIn(BaseModel):
    subscription_status: str = ""
    customer_email: str = ""
    current_period_end: float | None = None


@router.post("/aethos-identity/billing/webhook")
def billing_webhook_api(body: BillingWebhookIn) -> dict[str, Any]:
    """Flag-gated stub — maps subscription status → entitlement fields (Part E)."""
    from aethos_core.config import get_settings

    if not get_settings().billing_enabled:
        return {"ok": False, "error": "billing_disabled"}
    email = body.customer_email.strip().lower()
    if not email:
        return {"ok": False, "error": "customer_email_required"}
    status_map = {
        "active": "active",
        "trialing": "trial",
        "past_due": "suspended",
        "canceled": "revoked",
        "unpaid": "suspended",
    }
    entitlement_status = status_map.get(body.subscription_status.strip().lower(), "suspended")
    with _LOCK:
        store = _load_store()
        user_id = _resolve_owner_user_id(store, email)
        if not user_id:
            return {"ok": False, "error": "user_not_found"}
        user = store["users"][user_id]
        _normalize_entitlement(user)
        user["status"] = entitlement_status
        user["entitlement_source"] = "stripe"
        if body.current_period_end is not None:
            user["access_expires_at"] = float(body.current_period_end)
        if entitlement_status in {"revoked", "suspended"}:
            _revoke_user_sessions(store, user_id)
        _save_store(store)
    _audit(
        "billing.webhook",
        target=user_id,
        metadata={"subscription_status": body.subscription_status, "entitlement_status": entitlement_status},
    )
    return {
        "ok": True,
        "user_id": user_id,
        "status": entitlement_status,
        "entitlement_source": "stripe",
    }


@router.post("/aethos-identity/billing/checkout")
def billing_checkout_api(request: Request) -> dict[str, Any]:
    """Start a Stripe Checkout subscription for the signed-in user. Returns a checkout URL."""
    from aethos_core.auth.email_verification import public_app_base
    from aethos_core.billing.stripe_client import billing_configured, create_checkout_session

    if not billing_configured():
        return {"ok": False, "error": "billing_not_configured"}
    resolved = _session_from_request(request)
    if not resolved:
        return {"ok": False, "error": "not_authenticated"}
    _, user = resolved
    base = public_app_base(request)
    return create_checkout_session(
        customer_email=str(user.get("email") or ""),
        success_url=f"{base}/?billing=success",
        cancel_url=f"{base}/?billing=cancelled",
    )


@router.post("/aethos-identity/billing/stripe/webhook")
async def stripe_webhook_api(request: Request) -> Any:
    """Real Stripe webhook — HMAC-verified, maps subscription events → entitlement."""
    from aethos_core.billing.stripe_client import entitlement_from_event, verify_webhook

    payload = await request.body()
    event = verify_webhook(payload, request.headers.get("stripe-signature", ""))
    if event is None:
        return JSONResponse(status_code=400, content={"ok": False, "error": "invalid_signature"})
    update = entitlement_from_event(event)
    if not update:
        return {"ok": True, "ignored": str(event.get("type") or "")}

    with _LOCK:
        store = _load_store()
        user_id = _resolve_owner_user_id(store, update["email"])
        if not user_id:
            return {"ok": True, "user_not_found": True}
        user = store["users"][user_id]
        _normalize_entitlement(user)
        user["status"] = update["status"]
        user["plan"] = update["plan"]
        user["entitlement_source"] = "stripe"
        user["access_expires_at"] = update["access_expires_at"]
        if update["status"] in {"suspended", "expired", "revoked"}:
            _revoke_user_sessions(store, user_id)
        _save_store(store)
    _audit("billing.stripe_webhook", target=user_id, metadata={"type": event.get("type"), "status": update["status"]})
    return {"ok": True, "user_id": user_id, "status": update["status"]}

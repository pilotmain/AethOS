# SPDX-License-Identifier: Apache-2.0
"""§7 Role-based access control (least privilege) for human users.

Formalizes four human roles on top of the §2 auth user store and the existing
governance role architecture:

  * ``admin``     — full control, including user/role management and deployment
                    governance (kill switches) in multi-tenant mode.
  * ``approver``  — may grant/deny approvals (separation of duties: approves but
                    does not author or execute mutations).
  * ``operator``  — may operate the system: run actions, trigger mutations,
                    spawn agents (but cannot approve their own work).
  * ``read_only`` — may read everything, mutate nothing.

Enforcement is at the API middleware layer (the real security boundary): every
mutating request is mapped to a required permission and rejected with 403 if the
caller's roles don't grant it. Because the user record is re-read per request,
role changes take effect immediately. The UI consumes the same permission set
(via /aethos-identity/session) to hide controls, but the API is authoritative.
"""

from __future__ import annotations

# Permission vocabulary.
READ = "read"
OPERATE = "operate"
MUTATE = "mutate"
APPROVE = "approve"
SPAWN_AGENT = "spawn_agent"
MANAGE_USERS = "manage_users"
MANAGE_GOVERNANCE = "manage_governance"
OWN_PLATFORM = "own_platform"

ALL_PERMISSIONS = (
    READ,
    OPERATE,
    MUTATE,
    APPROVE,
    SPAWN_AGENT,
    MANAGE_USERS,
    MANAGE_GOVERNANCE,
    OWN_PLATFORM,
)

ROLE_PERMISSIONS: dict[str, set[str]] = {
    "admin": {READ, OPERATE, MUTATE, APPROVE, SPAWN_AGENT, MANAGE_USERS, MANAGE_GOVERNANCE},
    "tenant_admin": {READ, OPERATE, MUTATE, APPROVE, SPAWN_AGENT},
    "approver": {READ, APPROVE},
    "operator": {READ, OPERATE, MUTATE, SPAWN_AGENT},
    "read_only": {READ},
}

# Within-tenant powers for the primary user of a tenant (pairing approve, connections, deploy).
TENANT_OWNER_PERMISSIONS: frozenset[str] = frozenset(
    {READ, OPERATE, MUTATE, APPROVE, SPAWN_AGENT}
)

# Cross-tenant platform plane — billing, suspend/expire, owner admin APIs (env-only).
PLATFORM_OWNER_PERMISSIONS: frozenset[str] = frozenset({OWN_PLATFORM, MANAGE_USERS})

VALID_ROLES = tuple(ROLE_PERMISSIONS.keys())

_SAFE_METHODS = {"GET", "HEAD", "OPTIONS"}

# Path markers → required permission for mutating requests. First match wins.
_PATH_PERMISSION_RULES: tuple[tuple[str, str], ...] = (
    ("/aethos-identity/admin", OWN_PLATFORM),
    ("/aethos-identity/users", MANAGE_USERS),
    ("/governance/overrides", MANAGE_GOVERNANCE),
    ("/agents/spawn", SPAWN_AGENT),
    ("/approve", APPROVE),
    ("/approval", APPROVE),
    ("/mutations", MUTATE),
    ("/mutation", MUTATE),
    ("/execute", MUTATE),
)


def platform_owner_email_set() -> set[str]:
    from aethos_core.config import get_settings

    raw = getattr(get_settings(), "platform_owner_emails", "") or ""
    return {e.strip().lower() for e in raw.split(",") if e.strip()}


def is_platform_owner(user: dict[str, object] | None) -> bool:
    """Computed per request from PLATFORM_OWNER_EMAILS — never stored on the user.

    In self-host mode there is exactly one operator and they own their own
    instance, so owner rights are granted unconditionally."""
    from aethos_core.config import get_settings

    if getattr(get_settings(), "self_host", False):
        return True
    if not user:
        return False
    email = str(user.get("email") or user.get("user_id") or "").strip().lower()
    if not email:
        return False
    owners = platform_owner_email_set()
    return bool(owners) and email in owners


def tenant_for_user(user: dict[str, object] | None) -> str:
    """The tenant id this user belongs to (for RBAC before tenant_context middleware runs)."""
    from aethos_core.config import get_settings
    from aethos_core.tenancy import DEFAULT_TENANT, normalize_tenant

    if not user:
        return DEFAULT_TENANT
    if not get_settings().multi_tenant_enabled:
        return DEFAULT_TENANT
    return normalize_tenant(str(user.get("user_id") or user.get("email") or DEFAULT_TENANT))


def is_tenant_owner(user: dict[str, object] | None) -> bool:
    """True when the user is the primary owner of their tenant (tenant-scoped powers).

    Ownership is determined by tenancy first (``tenant == user_id`` in multi-tenant mode),
    not by stored role labels — so existing ``operator`` accounts keep approve within their tenant.
    ``tenant_admin`` / ``admin`` also confer owner powers when scoped to the user's tenant.
    """
    if not user or user.get("disabled"):
        return False
    user_id = str(user.get("user_id") or user.get("email") or "").strip().lower()
    if not user_id:
        return False
    from aethos_core.config import get_settings
    from aethos_core.tenancy import DEFAULT_TENANT

    tenant = tenant_for_user(user)
    roles = set(user.get("roles") or [])

    if get_settings().multi_tenant_enabled:
        if tenant == user_id:
            return True
        if ("tenant_admin" in roles or "admin" in roles) and tenant == user_id:
            return True
        return False

    if tenant != DEFAULT_TENANT:
        return tenant == user_id
    if "tenant_admin" in roles or "admin" in roles:
        return True
    return False


def permissions_for_roles(roles: list[str] | tuple[str, ...] | None) -> set[str]:
    perms: set[str] = set()
    for role in roles or []:
        perms |= ROLE_PERMISSIONS.get(role, set())
    return perms


def permissions_for_user(user: dict[str, object] | None) -> set[str]:
    roles = list(user.get("roles", []) if user else [])
    perms = permissions_for_roles(roles)
    # Account-owner elevation is the separation-of-duties waiver that lets a tenant's
    # own primary user approve their own work. It must NOT override an explicit
    # read-only lock: when the platform owner restricts a user to read_only, that
    # user stays read-only in their own account too (otherwise read_only is a no-op).
    if is_tenant_owner(user) and set(roles) != {"read_only"}:
        perms |= set(TENANT_OWNER_PERMISSIONS)
    if is_platform_owner(user):
        perms |= set(PLATFORM_OWNER_PERMISSIONS)
    return perms


def required_permission(method: str, path: str) -> str:
    """The permission a request needs. Reads require READ; writes are classified."""
    from aethos_core.tenancy.operator import operator_only_path

    if operator_only_path(path):
        return MANAGE_GOVERNANCE
    if method.upper() in _SAFE_METHODS:
        return READ
    for marker, perm in _PATH_PERMISSION_RULES:
        if marker in path:
            return perm
    return OPERATE


def is_authorized(
    roles: list[str] | tuple[str, ...] | None,
    method: str,
    path: str,
    *,
    user: dict[str, object] | None = None,
) -> bool:
    if user is not None:
        return required_permission(method, path) in permissions_for_user(user)
    return required_permission(method, path) in permissions_for_roles(roles)


def _auth_enforced() -> bool:
    from aethos_core.config import get_settings

    s = get_settings()
    return bool(s.auth_enabled) or bool(s.multi_tenant_enabled)


async def rbac_middleware(request, call_next):
    """Enforce least-privilege on authenticated requests (§7).

    No-op unless AUTH_ENABLED or MULTI_TENANT_ENABLED (shared mode implies auth).
    Operator-only governance paths require ``admin`` (``MANAGE_GOVERNANCE``) when
    multi-tenant is on — tenant ``operator`` role users cannot read or flip kill
    switches.
    """
    from starlette.responses import JSONResponse

    from aethos_core.config import get_settings
    from aethos_core.tenancy.operator import operator_only_path, require_deployment_operator

    if not _auth_enforced() or request.method == "OPTIONS":
        return await call_next(request)

    user = getattr(request.state, "user", None)
    path = request.url.path

    # Governance / deployment-control paths: defense-in-depth in shared mode.
    if get_settings().multi_tenant_enabled and operator_only_path(path):
        if user is None or not require_deployment_operator(user):
            return JSONResponse(
                {
                    "error": "forbidden",
                    "required_permission": MANAGE_GOVERNANCE,
                    "detail": "deployment_operator_required",
                    "roles": user.get("roles", []) if user else [],
                },
                status_code=403,
            )
        return await call_next(request)

    if request.method in _SAFE_METHODS:
        return await call_next(request)

    if user is None:
        return await call_next(request)

    if not is_authorized(user.get("roles", []), request.method, path, user=user):
        return JSONResponse(
            {
                "error": "forbidden",
                "required_permission": required_permission(request.method, path),
                "roles": user.get("roles", []),
            },
            status_code=403,
        )
    return await call_next(request)

# SPDX-License-Identifier: Apache-2.0
"""Declarative readonly inventory APIs — Mission Control vault tokens only."""

from __future__ import annotations

import base64
from dataclasses import dataclass, field
from typing import Any, Callable

import httpx


@dataclass(frozen=True)
class HttpInventorySpec:
    provider: str
    url: str
    auth: str = "bearer"  # bearer | stripe_basic | sentry_bearer | header_api_key
    list_path: str | None = None  # dotted path to list in JSON body; None = body is list
    name_fields: tuple[str, ...] = ("name",)
    status_fields: tuple[str, ...] = ("status", "state")
    extra_headers: dict[str, str] = field(default_factory=dict)
    header_api_key_name: str = ""


def _http_get(spec: HttpInventorySpec, token: str) -> dict[str, Any]:
    hdrs = dict(spec.extra_headers)
    raw = token.strip()
    if spec.auth == "bearer":
        hdrs["Authorization"] = f"Bearer {raw}"
    elif spec.auth == "stripe_basic":
        hdrs["Authorization"] = f"Basic {base64.b64encode(f'{raw}:'.encode()).decode()}"
    elif spec.auth == "sentry_bearer":
        hdrs["Authorization"] = f"Bearer {raw}"
    elif spec.auth == "header_api_key" and spec.header_api_key_name:
        hdrs[spec.header_api_key_name] = raw
    try:
        with httpx.Client(timeout=25.0) as client:
            resp = client.get(spec.url, headers=hdrs)
        if resp.status_code >= 400:
            return {"ok": False, "error": f"HTTP {resp.status_code}", "url": spec.url}
        try:
            body = resp.json()
        except Exception:
            body = {"raw": resp.text[:500]}
        return {"ok": True, "body": body, "url": spec.url}
    except httpx.HTTPError as exc:
        return {"ok": False, "error": str(exc), "url": spec.url}


def _dig(obj: Any, path: str | None) -> Any:
    if path is None:
        return obj
    cur = obj
    for part in path.split("."):
        if not isinstance(cur, dict):
            return None
        cur = cur.get(part)
    return cur


def _field(row: dict[str, Any], fields: tuple[str, ...]) -> Any:
    for key in fields:
        if key in row and row[key] not in (None, ""):
            return row[key]
        nested = row.get("service") if isinstance(row.get("service"), dict) else None
        if isinstance(nested, dict) and key in nested:
            return nested.get(key)
    return None


def fetch_http_inventory(spec: HttpInventorySpec, token: str) -> dict[str, Any]:
    payload = _http_get(spec, token)
    if not payload.get("ok"):
        return {"ok": False, "error": payload.get("error"), "resources": [], "provider": spec.provider}
    body = payload.get("body")
    rows_raw = _dig(body, spec.list_path)
    if rows_raw is None:
        rows_raw = body
    rows = rows_raw if isinstance(rows_raw, list) else list((rows_raw or {}).get("items") or []) if isinstance(rows_raw, dict) else []
    resources: list[dict[str, Any]] = []
    for row in rows[:50]:
        if not isinstance(row, dict):
            continue
        svc = row.get("service") if isinstance(row.get("service"), dict) else row
        if not isinstance(svc, dict):
            continue
        resources.append(
            {
                "name": _field(svc, spec.name_fields) or _field(row, spec.name_fields),
                "status": _field(svc, spec.status_fields) or _field(row, spec.status_fields) or "unknown",
                "raw_type": svc.get("type") or row.get("type"),
            }
        )
    return {"ok": True, "provider": spec.provider, "resource_count": len(resources), "resources": resources}


# Legacy bespoke fetchers (Render nested service shape, etc.)
def fetch_render_inventory(token: str) -> dict[str, Any]:
    return fetch_http_inventory(
        HttpInventorySpec(
            provider="render",
            url="https://api.render.com/v1/services?limit=50",
            list_path=None,
            name_fields=("name", "slug"),
            status_fields=("state",),
        ),
        token,
    )


def fetch_netlify_inventory(token: str) -> dict[str, Any]:
    spec = HttpInventorySpec(
        provider="netlify",
        url="https://api.netlify.com/api/v1/sites?per_page=50",
        name_fields=("name",),
        status_fields=("state",),
    )
    payload = _http_get(spec, token)
    if not payload.get("ok"):
        return {"ok": False, "error": payload.get("error"), "resources": []}
    body = payload.get("body")
    rows = body if isinstance(body, list) else []
    resources = [
        {
            "name": row.get("name"),
            "status": row.get("state") or "unknown",
            "url": row.get("ssl_url") or row.get("url"),
        }
        for row in rows[:50]
        if isinstance(row, dict)
    ]
    return {"ok": True, "resource_count": len(resources), "resources": resources, "provider": "netlify"}


HTTP_INVENTORY_SPECS: dict[str, HttpInventorySpec] = {
    "digitalocean": HttpInventorySpec(
        provider="digitalocean",
        url="https://api.digitalocean.com/v2/droplets?per_page=50",
        list_path="droplets",
        name_fields=("name",),
        status_fields=("status",),
    ),
    "fly": HttpInventorySpec(
        provider="fly",
        url="https://api.machines.dev/v1/apps",
        extra_headers={"Accept": "application/json"},
        name_fields=("name", "id"),
        status_fields=("status",),
    ),
    "heroku": HttpInventorySpec(
        provider="heroku",
        url="https://api.heroku.com/apps",
        extra_headers={"Accept": "application/vnd.heroku+json; version=3"},
        name_fields=("name",),
        status_fields=("state",),
    ),
    "cloudflare": HttpInventorySpec(
        provider="cloudflare",
        url="https://api.cloudflare.com/client/v4/zones?per_page=50",
        list_path="result",
        name_fields=("name",),
        status_fields=("status",),
    ),
    "supabase": HttpInventorySpec(
        provider="supabase",
        url="https://api.supabase.com/v1/projects",
        name_fields=("name",),
        status_fields=("status",),
    ),
    "sentry": HttpInventorySpec(
        provider="sentry",
        url="https://sentry.io/api/0/projects/",
        auth="sentry_bearer",
        name_fields=("name", "slug"),
        status_fields=("status",),
    ),
    "stripe": HttpInventorySpec(
        provider="stripe",
        url="https://api.stripe.com/v1/products?limit=25",
        auth="stripe_basic",
        list_path="data",
        name_fields=("name",),
        status_fields=("active",),
    ),
    "resend": HttpInventorySpec(
        provider="resend",
        url="https://api.resend.com/domains",
        name_fields=("name",),
        status_fields=("status",),
    ),
    "openai": HttpInventorySpec(
        provider="openai",
        url="https://api.openai.com/v1/models",
        list_path="data",
        name_fields=("id",),
        status_fields=("owned_by",),
    ),
    "linode": HttpInventorySpec(
        provider="linode",
        url="https://api.linode.com/v4/linode/instances",
        list_path="data",
        name_fields=("label",),
        status_fields=("status",),
    ),
    "hetzner": HttpInventorySpec(
        provider="hetzner",
        url="https://api.hetzner.cloud/v1/servers",
        list_path="servers",
        name_fields=("name",),
        status_fields=("status",),
    ),
}


CUSTOM_INVENTORY_FETCHERS: dict[str, Callable[[str], dict[str, Any]]] = {
    "render": fetch_render_inventory,
    "netlify": fetch_netlify_inventory,
}


def fetch_provider_inventory(provider: str, token: str) -> dict[str, Any]:
    key = (provider or "").strip().lower()
    custom = CUSTOM_INVENTORY_FETCHERS.get(key)
    if custom is not None:
        out = custom(token)
        out.setdefault("provider", key)
        return out
    spec = HTTP_INVENTORY_SPECS.get(key)
    if spec is not None:
        return fetch_http_inventory(spec, token)
    return {
        "ok": True,
        "provider": key,
        "resource_count": 0,
        "resources": [],
        "message": "credential_validated_no_list_api",
    }


# Backward-compatible export
TOKEN_INVENTORY_FETCHERS: dict[str, Callable[[str], dict[str, Any]]] = {
    **{k: lambda t, s=HTTP_INVENTORY_SPECS[k]: fetch_http_inventory(s, t) for k in HTTP_INVENTORY_SPECS},
    **CUSTOM_INVENTORY_FETCHERS,
}

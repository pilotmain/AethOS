# SPDX-License-Identifier: Apache-2.0
"""Probe secure env value sources — presence only, never return secret values."""

from __future__ import annotations

import os
import re
from pathlib import Path
from typing import Any

from aethos_core.providers.railway.env_value_readiness.env_classification import (
    EnvCriticality,
    classify_env_var,
    default_runtime_value,
    infer_deployment_profile,
    is_secret_env_name,
)
from aethos_core.providers.railway.env_value_readiness.env_value_readiness import (
    _PROVIDER_ENV_MAP,
    build_target_key,
)


def _presence_entry(
    *,
    present: bool,
    source: str | None,
    secret: bool,
    using_default: bool = False,
    default_value: str | None = None,
) -> dict[str, Any]:
    entry: dict[str, Any] = {
        "present": bool(present),
        "source": source,
        "secret": bool(secret),
        "using_default": bool(using_default),
    }
    if default_value is not None:
        entry["default_value"] = default_value
    return entry


def _deployment_env_presence_path(target_key: str) -> Path:
    from aethos_core.tenancy.tenant_data_store import resolve_data_tenant

    safe = re.sub(r"[^a-zA-Z0-9_|.-]+", "_", target_key)[:180]
    tenant = resolve_data_tenant()
    root = (
        Path(__file__).resolve().parents[3]
        / "data"
        / "railway_deployment_env_presence"
        / tenant
    )
    root.mkdir(parents=True, exist_ok=True)
    return root / f"{safe}.json"


def _load_deployment_env_presence(target_key: str) -> set[str]:
    import json

    path = _deployment_env_presence_path(target_key)
    if not path.is_file():
        return set()
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return set()
    if not isinstance(raw, dict):
        return set()
    names = raw.get("present_names") or raw.get("configured_names") or []
    return {str(n).strip().upper() for n in names if str(n).strip()}


def set_deployment_env_presence_for_tests(
    *,
    target_key: str,
    present_names: list[str],
) -> None:
    import json
    from datetime import UTC, datetime

    path = _deployment_env_presence_path(target_key)
    path.write_text(
        json.dumps(
            {
                "present_names": list(present_names),
                "updated_at": datetime.now(UTC).isoformat(),
            },
            indent=2,
        ),
        encoding="utf-8",
    )


def clear_deployment_env_presence_for_tests() -> None:
    base = Path(__file__).resolve().parents[3] / "data" / "railway_deployment_env_presence"
    if base.is_dir():
        for path in base.rglob("*.json"):
            path.unlink()


def _local_trusted_secret_value(name: str) -> str:
    """Solo/local dev: read from process env or pydantic Settings (.env file) when explicitly trusted."""
    from aethos_core.governance.approval_privacy_governance import local_env_trusted_or_empty

    if not local_env_trusted_or_empty():
        return ""
    upper = (name or "").strip().upper()
    if not upper:
        return ""
    direct = str(os.environ.get(upper) or "").strip()
    if direct:
        return direct
    try:
        from aethos_core.config import get_settings

        field = upper.lower()
        settings = get_settings()
        if hasattr(settings, field):
            return str(getattr(settings, field) or "").strip()
    except Exception:
        return ""

    if upper == "NEXT_PUBLIC_API_BASE":
        for rel in ("web/.env.local", "web/.env"):
            path = Path(__file__).resolve().parents[4] / rel
            if not path.is_file():
                continue
            try:
                for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
                    if line.strip().startswith("#") or "=" not in line:
                        continue
                    key, _, value = line.partition("=")
                    if key.strip().upper() == upper:
                        return value.strip().strip("'\"")
            except OSError:
                continue
    return ""


def _local_env_present(name: str) -> bool:
    return bool(_local_trusted_secret_value(name))


def _credential_center_provider_token_present(provider: str) -> bool:
    try:
        from aethos_core.credentials import get_provider_api_token

        token = get_provider_api_token(provider)
        return bool(token and str(token).strip())
    except Exception:
        return False


def _secure_store_reference_present(name: str, *, target_key: str) -> bool:
    return name.strip().upper() in _load_deployment_env_presence(target_key)


def _credential_center_named_secret_present(name: str, *, target_key: str) -> bool:
    upper = name.strip().upper()
    provider = _PROVIDER_ENV_MAP.get(upper)
    if provider and _credential_center_provider_token_present(provider):
        return True
    try:
        from aethos_core.security.credential_vault import get_credential_vault

        vault = get_credential_vault()
        for rec in vault.list_credentials():
            label = str(rec.label or "").upper()
            if upper in label or label == upper:
                secret = vault.retrieve_secret(rec.credential_id) or {}
                if str(secret.get("token") or "").strip():
                    return True
    except Exception:
        pass
    return False


def probe_env_var_presence(
    name: str,
    *,
    plan: dict[str, Any],
    profile: str | None = None,
) -> dict[str, Any]:
    env_name = (name or "").strip()
    profile = profile or infer_deployment_profile(plan)
    criticality = classify_env_var(env_name, profile=profile)
    secret = criticality == EnvCriticality.CRITICAL_SECRET or is_secret_env_name(env_name)
    target_key = build_target_key(
        repo=str(plan.get("repo") or ""),
        project=str(plan.get("project") or ""),
        environment=str(plan.get("environment") or ""),
        service_name=str(plan.get("service_name") or ""),
    )

    if secret and _credential_center_named_secret_present(env_name, target_key=target_key):
        return _presence_entry(present=True, source="credential_center", secret=True)

    if secret and _secure_store_reference_present(env_name, target_key=target_key):
        return _presence_entry(present=True, source="secure_store_reference", secret=True)

    if secret and _local_env_present(env_name):
        return _presence_entry(present=True, source="local_env_dev_only", secret=True)

    if not secret and _local_env_present(env_name):
        return _presence_entry(present=True, source="local_env_dev_only", secret=False)

    return _presence_entry(present=False, source=None, secret=secret)

# SPDX-License-Identifier: Apache-2.0
"""Connection credential metadata — no raw secrets in public shapes."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from time import time
from typing import Any
from uuid import uuid4

from aethos_core.connections.validation_status import CONFIGURED


class CredentialType(str, Enum):
    BROWSER_SESSION = "browser_session"
    API_TOKEN = "api_token"
    USERNAME_PASSWORD = "username_password"
    CLI_AUTH = "cli_auth"
    OAUTH_TOKEN = "oauth_token"


class AuthMethod(str, Enum):
    API_TOKEN = "api_token"
    BROWSER = "browser"
    CLI = "cli"
    USERNAME_PASSWORD = "username_password"
    ASK = "ask"


def _new_credential_id() -> str:
    return f"cred-{uuid4().hex[:12]}"


@dataclass
class CredentialRecord:
    credential_id: str
    provider: str
    type: CredentialType
    label: str
    # Owning tenant. "default" is the operator/single-tenant owner; existing
    # global credentials migrate to it on first load (see CredentialVault._load),
    # so single-tenant behavior is unchanged. In multi-tenant mode the vault
    # filters every access by the current tenant so one tenant's secrets are
    # invisible to another (Phase 2).
    owner_id: str = "default"
    created_at: float = field(default_factory=time)
    last_used_at: float | None = None
    last_tested_at: float | None = None
    last_test_ok: bool | None = None
    expires_at: float | None = None
    revoked: bool = False
    scope: list[str] = field(default_factory=list)
    write_allowed: bool = False
    storage: str = "encrypted_file"
    masked_identifier: str = ""
    validation_status: str = CONFIGURED
    last_validated_at: float | None = None
    updated_at: float | None = None
    validation_diagnostics: dict[str, Any] = field(default_factory=dict)

    def to_public_dict(self) -> dict[str, Any]:
        return {
            "credential_id": self.credential_id,
            "provider": self.provider,
            "type": self.type.value,
            "label": self.label,
            "owner_id": self.owner_id,
            "created_at": self.created_at,
            "updated_at": self.updated_at or self.created_at,
            "last_used_at": self.last_used_at,
            "last_tested_at": self.last_tested_at,
            "last_test_ok": self.last_test_ok,
            "last_validated_at": self.last_validated_at,
            "validation_status": self.validation_status,
            "validation_diagnostics": dict(self.validation_diagnostics),
            "expires_at": self.expires_at,
            "revoked": self.revoked,
            "scope": list(self.scope),
            "write_allowed": self.write_allowed,
            "storage": self.storage,
            "masked_identifier": self.masked_identifier,
            "token_preview": self.masked_identifier,
        }


@dataclass
class ProviderConnectionStatus:
    provider: str
    preferred_method: AuthMethod = AuthMethod.ASK
    api_token: str = "missing"  # configured | missing | revoked
    browser_session: str = "missing"
    cli_auth: str = "not_detected"
    username_password: str = "missing"
    credentials: list[dict[str, Any]] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "provider": self.provider,
            "preferred_method": self.preferred_method.value,
            "connected_methods": {
                "api_token": self.api_token,
                "browser_session": self.browser_session,
                "cli_auth": self.cli_auth,
                "username_password": self.username_password,
            },
            "credentials": self.credentials,
        }

# SPDX-License-Identifier: Apache-2.0
"""AWS auth adapter — FUNCTIONALITY_REALITY_SPRINT_001 readonly phase."""

from __future__ import annotations

from typing import Any

from aethos_core.connections.credential_state import connection_api_token_status
from aethos_core.connections.models import AuthMethod, ProviderConnectionStatus
from aethos_core.providers.base.auth_adapter import AuthAdapter
from aethos_core.security.credential_vault import get_credential_vault


class AwsAuthAdapter(AuthAdapter):
    provider = "aws"

    def list_credentials(self) -> list[dict[str, Any]]:
        return [c.to_public_dict() for c in get_credential_vault().list_credentials(provider=self.provider)]

    def connection_status(self) -> ProviderConnectionStatus:
        api_token = connection_api_token_status(provider=self.provider)
        return ProviderConnectionStatus(
            provider=self.provider,
            preferred_method=AuthMethod.API_TOKEN,
            api_token=api_token,
            browser_session="missing",
            cli_auth="not_detected",
            username_password="missing",
            credentials=self.list_credentials(),
        )

    def resolve_best_auth_method(self, *, operation: str = "read") -> dict[str, Any]:
        _ = operation
        creds = self.list_credentials()
        if creds:
            cid = str(creds[0].get("credential_id") or creds[0].get("id") or "")
            if cid:
                return {"method": "api_token", "credential_id": cid, "detail": None}
        return {
            "method": None,
            "credential_id": None,
            "detail": "AWS credentials not configured — add access key in Mission Control → Advanced settings → Credentials.",
        }

    def test_credential(self, credential_id: str) -> dict[str, Any]:
        from aethos_core.providers.cloud.validators import validate_aws_token

        rec = get_credential_vault().get(credential_id)
        if not rec or rec.provider != self.provider:
            raise KeyError(credential_id)
        secret = get_credential_vault().retrieve_secret(credential_id) or {}
        token = str(secret.get("token") or "").strip()
        if not token:
            return {"ok": False, "detail": "Credential secret missing or not decryptable."}
        return validate_aws_token(token)

    def revoke_credential(self, credential_id: str) -> bool:
        return get_credential_vault().revoke(credential_id)

    def get_api_token(self, credential_id: str) -> str | None:
        from aethos_core.operations.orchestration.provider_runtime import get_provider_api_token

        return get_provider_api_token(provider="aws", auth={"credential_id": credential_id}, require_validated=False)

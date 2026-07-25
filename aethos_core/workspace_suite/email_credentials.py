# SPDX-License-Identifier: Apache-2.0
"""Per-tenant IMAP/SMTP credentials for workspace email — vault-backed JSON blob."""

from __future__ import annotations

import json
import imaplib
from dataclasses import dataclass
from typing import Any

from aethos_core.security.credential_vault import get_credential_vault
from aethos_core.security.secret_redaction import mask_secret, redact_text

EMAIL_IMAP_PROVIDER = "email_imap"


@dataclass(frozen=True)
class EmailCredentialField:
    id: str
    label: str
    secret: bool = False
    required: bool = True
    placeholder: str = ""
    help: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "label": self.label,
            "secret": self.secret,
            "required": self.required,
            "placeholder": self.placeholder,
            "help": self.help,
        }


def _f(id: str, label: str, **kw: Any) -> EmailCredentialField:
    return EmailCredentialField(id=id, label=label, **kw)


EMAIL_IMAP_FIELDS: tuple[EmailCredentialField, ...] = (
    _f("imap_host", "IMAP host", secret=False, placeholder="imap.gmail.com"),
    _f("imap_port", "IMAP port", secret=False, required=False, placeholder="993", help="Default 993 (SSL)."),
    _f("imap_user", "IMAP username", secret=False, placeholder="you@example.com"),
    _f("imap_password", "IMAP password", secret=True, placeholder="App password or IMAP secret"),
    _f("imap_mailbox", "Mailbox", secret=False, required=False, placeholder="INBOX", help="Default INBOX."),
    _f("smtp_host", "SMTP host (optional)", secret=False, required=False, placeholder="smtp.gmail.com"),
    _f("smtp_port", "SMTP port (optional)", secret=False, required=False, placeholder="587"),
    _f("smtp_user", "SMTP username (optional)", secret=False, required=False),
    _f("smtp_password", "SMTP password (optional)", secret=True, required=False),
)

EMAIL_IMAP_SCHEMA: dict[str, Any] = {
    "service_id": EMAIL_IMAP_PROVIDER,
    "label": "Email (IMAP/SMTP)",
    "primary_field": "imap_user",
    "default_label": "Personal inbox",
    "description": "Per-account inbox credentials for Workspace → Email triage. Secrets stay in the encrypted vault.",
    "fields": [f.to_dict() for f in EMAIL_IMAP_FIELDS],
}


class EmailCredentialError(ValueError):
    """Invalid email credential payload."""


def _parse_blob(raw: str) -> dict[str, str]:
    raw = (raw or "").strip()
    if not raw:
        return {}
    if raw.startswith("{"):
        try:
            parsed = json.loads(raw)
            return {str(k): str(v) for k, v in parsed.items()} if isinstance(parsed, dict) else {}
        except (json.JSONDecodeError, TypeError):
            return {}
    return {}


def store_email_imap_credentials(*, label: str, fields: dict[str, str]) -> Any:
    cleaned: dict[str, str] = {}
    for spec in EMAIL_IMAP_FIELDS:
        value = str(fields.get(spec.id) or "").strip()
        if spec.required and not value:
            raise EmailCredentialError(f"{spec.label} is required.")
        if value:
            cleaned[spec.id] = value
    if not cleaned.get("imap_host") or not cleaned.get("imap_user") or not cleaned.get("imap_password"):
        raise EmailCredentialError("IMAP host, username, and password are required.")
    if not cleaned.get("imap_port"):
        cleaned["imap_port"] = "993"
    if not cleaned.get("imap_mailbox"):
        cleaned["imap_mailbox"] = "INBOX"
    blob = json.dumps(cleaned, separators=(",", ":"))
    record = get_credential_vault().store_api_token(
        provider=EMAIL_IMAP_PROVIDER,
        label=(label or EMAIL_IMAP_SCHEMA["default_label"]).strip(),
        token=blob,
        scope=["email_read", "email_send"],
        write_allowed=False,
        masked_identifier=mask_secret(cleaned["imap_user"], visible=4),
    )
    return record


def resolve_email_imap_fields() -> dict[str, str]:
    vault = get_credential_vault()
    creds = [c for c in vault.list_credentials(provider=EMAIL_IMAP_PROVIDER) if not c.revoked]
    if not creds:
        return {}
    creds.sort(key=lambda c: (c.last_used_at or c.created_at or 0), reverse=True)
    for cred in creds:
        fields = _parse_blob(str((vault.retrieve_secret(cred.credential_id) or {}).get("token") or ""))
        if fields.get("imap_host") and fields.get("imap_user"):
            return fields
    return {}


def email_has_vault_credentials() -> bool:
    fields = resolve_email_imap_fields()
    return bool(fields.get("imap_host") and fields.get("imap_user") and fields.get("imap_password"))


def resolve_email_imap_connection() -> dict[str, str] | None:
    """Normalized IMAP connection dict for triage (host, user, password, mailbox, port)."""
    fields = resolve_email_imap_fields()
    if not fields.get("imap_host") or not fields.get("imap_user"):
        return None
    try:
        port = int(str(fields.get("imap_port") or "993").strip() or "993")
    except ValueError:
        port = 993
    return {
        "host": str(fields["imap_host"]),
        "user": str(fields["imap_user"]),
        "password": str(fields.get("imap_password") or ""),
        "mailbox": str(fields.get("imap_mailbox") or "INBOX"),
        "port": str(port),
    }


def list_email_imap_credentials() -> list[dict[str, Any]]:
    return [
        c.to_public_dict()
        for c in get_credential_vault().list_credentials(provider=EMAIL_IMAP_PROVIDER)
        if not c.revoked
    ]


def _imap_login(fields: dict[str, str]) -> dict[str, Any]:
    host = str(fields.get("imap_host") or "").strip()
    user = str(fields.get("imap_user") or "").strip()
    password = str(fields.get("imap_password") or "")
    if not host or not user or not password:
        return {"ok": False, "detail": "IMAP host, username, and password are required."}
    try:
        port = int(str(fields.get("imap_port") or "993").strip() or "993")
    except ValueError:
        port = 993
    mailbox = str(fields.get("imap_mailbox") or "INBOX").strip() or "INBOX"
    try:
        conn = imaplib.IMAP4_SSL(host, port, timeout=20)
        conn.login(user, password)
        conn.select(mailbox, readonly=True)
        conn.logout()
        return {"ok": True, "detail": f"IMAP login OK for {user} on {host}."}
    except Exception as exc:  # noqa: BLE001
        return {"ok": False, "detail": redact_text(str(exc))[:300]}


def test_email_imap_credential(credential_id: str) -> dict[str, Any]:
    vault = get_credential_vault()
    rec = vault.get(credential_id)
    if not rec or rec.provider != EMAIL_IMAP_PROVIDER:
        raise KeyError(credential_id)
    fields = _parse_blob(str((vault.retrieve_secret(credential_id) or {}).get("token") or ""))
    if not fields:
        return {"ok": False, "detail": "Credential secret missing or not decryptable."}
    return _imap_login(fields)


def revoke_email_imap_credential(credential_id: str) -> bool:
    vault = get_credential_vault()
    rec = vault.get(credential_id)
    if not rec or rec.provider != EMAIL_IMAP_PROVIDER:
        return False
    return vault.revoke(credential_id)


def email_connection_payload() -> dict[str, Any]:
    from aethos_core.security.credential_vault import get_credential_vault_diagnostics

    configured = email_has_vault_credentials()
    return {
        "ok": True,
        "service": EMAIL_IMAP_PROVIDER,
        "supports_credentials": True,
        "schema": EMAIL_IMAP_SCHEMA,
        "configured": configured,
        "credentials": list_email_imap_credentials(),
        "credential_vault": get_credential_vault_diagnostics(),
    }

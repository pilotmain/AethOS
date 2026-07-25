# SPDX-License-Identifier: Apache-2.0
"""Credential Center UI metadata — backend source of truth for Connections panels."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class CredentialUiConfig:
    manage_credentials: bool = True
    label: str = ""
    default_cred_label: str = ""
    token_field_label: str = "API token"
    description: str = ""
    security_note: str = "Stored in the encrypted vault — never shown again after save."
    supports_preferred_auth: bool = False
    token_placeholder: str = "Paste token here"

    def to_dict(self) -> dict[str, Any]:
        return {
            "manage_credentials": self.manage_credentials,
            "label": self.label,
            "default_cred_label": self.default_cred_label,
            "token_field_label": self.token_field_label,
            "description": self.description,
            "security_note": self.security_note,
            "supports_preferred_auth": self.supports_preferred_auth,
            "token_placeholder": self.token_placeholder,
        }


VERCEL_CREDENTIAL_UI = CredentialUiConfig(
    label="Vercel",
    default_cred_label="Vercel primary account",
    token_field_label="Vercel API token",
    description=(
        "Connect Vercel with an API token or saved browser session for inventory, deploy diagnostics, and E2E orchestration."
    ),
    security_note="Paste your Vercel API token here. It is stored in the encrypted vault and never shown again.",
    supports_preferred_auth=True,
)

RAILWAY_CREDENTIAL_UI = CredentialUiConfig(
    label="Railway",
    default_cred_label="Railway primary account",
    token_field_label="Railway API token",
    description="Connect Railway for read-only inventory, deployment logs, greenfield deploy, and diagnostics.",
    security_note="AethOS never displays saved tokens after storage. Token is stored in the encrypted credential vault.",
)

GITHUB_CREDENTIAL_UI = CredentialUiConfig(
    label="GitHub",
    default_cred_label="GitHub primary account",
    token_field_label="GitHub personal access token",
    description="Connect GitHub for repository inspection, Actions diagnostics, and software delivery flows.",
    security_note="AethOS never displays saved tokens after storage. Token is stored in the encrypted credential vault.",
)


def cloud_credential_ui(
    *,
    label: str,
    token_field_label: str,
    description: str,
    token_placeholder: str = "Paste token here",
    default_cred_label: str = "",
    security_note: str = "Stored in the encrypted vault — never shown again after save.",
) -> CredentialUiConfig:
    return CredentialUiConfig(
        label=label,
        default_cred_label=default_cred_label or f"{label} primary account",
        token_field_label=token_field_label,
        description=description,
        security_note=security_note,
        token_placeholder=token_placeholder,
    )


AWS_CREDENTIAL_UI = cloud_credential_ui(
    label="AWS",
    token_field_label="AWS access key",
    token_placeholder="AKIA…:secret or JSON key",
    description="Connect AWS with an IAM access key pair or JSON credentials for inventory and operational checks.",
)

GCP_CREDENTIAL_UI = cloud_credential_ui(
    label="GCP",
    token_field_label="GCP service account JSON",
    token_placeholder='{"type":"service_account",…}',
    description="Connect Google Cloud with a service account JSON key or OAuth access token.",
)

AZURE_CREDENTIAL_UI = cloud_credential_ui(
    label="Azure",
    token_field_label="Azure credential",
    token_placeholder="Bearer token or service principal JSON",
    description="Connect Microsoft Azure with a bearer token or service principal credentials.",
)

CLOUDFLARE_CREDENTIAL_UI = cloud_credential_ui(
    label="Cloudflare",
    token_field_label="Cloudflare API token",
    description="Connect Cloudflare for DNS, Workers, and edge configuration inventory.",
)

DIGITALOCEAN_CREDENTIAL_UI = cloud_credential_ui(
    label="DigitalOcean",
    token_field_label="DigitalOcean API token",
    description="Connect DigitalOcean for droplets, apps, and infrastructure inventory.",
)

FLY_CREDENTIAL_UI = cloud_credential_ui(
    label="Fly.io",
    token_field_label="Fly.io API token",
    description="Connect Fly.io for app inventory and deployment diagnostics.",
)

RENDER_CREDENTIAL_UI = cloud_credential_ui(
    label="Render",
    token_field_label="Render API token",
    description="Connect Render for service inventory and deployment status.",
)

NETLIFY_CREDENTIAL_UI = cloud_credential_ui(
    label="Netlify",
    token_field_label="Netlify personal access token",
    description="Connect Netlify for site inventory and deploy diagnostics.",
)

HEROKU_CREDENTIAL_UI = cloud_credential_ui(
    label="Heroku",
    token_field_label="Heroku API key",
    description="Connect Heroku for app inventory and dyno diagnostics.",
)

SUPABASE_CREDENTIAL_UI = cloud_credential_ui(
    label="Supabase",
    token_field_label="Supabase Personal Access Token (account-wide)",
    token_placeholder="sbp_…",
    description=(
        "Account → Access Tokens in the Supabase dashboard. One token covers all your projects — "
        "AethOS lists your projects and fetches each project's keys on demand, so you don't hand-enter "
        "per-project keys. Per-project keys (URL / anon / service_role) remain supported via .env for "
        "direct single-project DB connections."
    ),
    security_note=(
        "Stored in the encrypted vault — never shown again after save. The PAT is account-wide; scope "
        "and rotate it like an admin credential."
    ),
)

STRIPE_CREDENTIAL_UI = cloud_credential_ui(
    label="Stripe",
    token_field_label="Stripe secret key",
    token_placeholder="sk_live_… or sk_test_…",
    description="Connect Stripe for billing and payment operational checks.",
    security_note="Secret keys are stored encrypted and never displayed after save.",
)

OPENAI_CREDENTIAL_UI = cloud_credential_ui(
    label="OpenAI",
    token_field_label="OpenAI API key",
    description="Connect OpenAI for model access and usage diagnostics.",
)

ANTHROPIC_CREDENTIAL_UI = cloud_credential_ui(
    label="Anthropic",
    token_field_label="Anthropic API key",
    token_placeholder="sk-ant-…",
    description="Connect Anthropic for Claude model access and diagnostics.",
)


def _model_credential_ui(*, label: str, placeholder: str = "Paste API key here") -> CredentialUiConfig:
    return cloud_credential_ui(
        label=label,
        token_field_label=f"{label} API key",
        token_placeholder=placeholder,
        description=f"Connect {label} so you can select its models in chat and Compare.",
        security_note="Stored in the encrypted vault — never shown again after save. This is your own key.",
    )


# §2 — bring-your-own-model providers (OpenAI + Anthropic above already exist).
GEMINI_CREDENTIAL_UI = _model_credential_ui(label="Google Gemini", placeholder="AIza…")
MISTRAL_CREDENTIAL_UI = _model_credential_ui(label="Mistral")
GROQ_CREDENTIAL_UI = _model_credential_ui(label="Groq", placeholder="gsk_…")
XAI_CREDENTIAL_UI = _model_credential_ui(label="xAI (Grok)", placeholder="xai-…")
DEEPSEEK_CREDENTIAL_UI = _model_credential_ui(label="DeepSeek", placeholder="sk-…")
COHERE_CREDENTIAL_UI = _model_credential_ui(label="Cohere")
TOGETHER_CREDENTIAL_UI = _model_credential_ui(label="Together")
FIREWORKS_CREDENTIAL_UI = _model_credential_ui(label="Fireworks", placeholder="fw_…")
PERPLEXITY_CREDENTIAL_UI = _model_credential_ui(label="Perplexity", placeholder="pplx-…")
OPENROUTER_CREDENTIAL_UI = _model_credential_ui(label="OpenRouter", placeholder="sk-or-…")

TAVILY_CREDENTIAL_UI = cloud_credential_ui(
    label="Tavily",
    token_field_label="Tavily API key",
    description="Connect Tavily for web search tool access.",
)

RESEND_CREDENTIAL_UI = cloud_credential_ui(
    label="Resend",
    token_field_label="Resend API key",
    description="Connect Resend for email delivery diagnostics.",
)

DATADOG_CREDENTIAL_UI = cloud_credential_ui(
    label="Datadog",
    token_field_label="Datadog API key",
    description="Connect Datadog for observability and incident diagnostics.",
)

MONGODB_ATLAS_CREDENTIAL_UI = cloud_credential_ui(
    label="MongoDB Atlas",
    token_field_label="MongoDB Atlas API key",
    token_placeholder="public:private key pair or OAuth token",
    description="Connect MongoDB Atlas for cluster inventory and diagnostics.",
)

PLAID_CREDENTIAL_UI = cloud_credential_ui(
    label="Plaid",
    token_field_label="Plaid credential",
    token_placeholder="client_id:secret or access token",
    description="Connect Plaid for financial data integration diagnostics.",
)

ORACLE_CLOUD_CREDENTIAL_UI = cloud_credential_ui(
    label="Oracle Cloud",
    token_field_label="OCI API key",
    token_placeholder="tenancy:user:region:key_fingerprint:private_key",
    description="Connect Oracle Cloud Infrastructure for inventory and operational checks.",
)

IBM_CLOUD_CREDENTIAL_UI = cloud_credential_ui(
    label="IBM Cloud",
    token_field_label="IBM Cloud API key",
    description="Connect IBM Cloud for resource inventory and diagnostics.",
)

LINODE_CREDENTIAL_UI = cloud_credential_ui(
    label="Linode (Akamai)",
    token_field_label="Linode personal access token",
    description="Connect Linode for compute and infrastructure inventory.",
)

SCALEWAY_CREDENTIAL_UI = cloud_credential_ui(
    label="Scaleway",
    token_field_label="Scaleway secret key",
    description="Connect Scaleway for instance and infrastructure inventory.",
)

HETZNER_CREDENTIAL_UI = cloud_credential_ui(
    label="Hetzner Cloud",
    token_field_label="Hetzner Cloud API token",
    description="Connect Hetzner Cloud for server inventory and diagnostics.",
)

TWILIO_CREDENTIAL_UI = cloud_credential_ui(
    label="Twilio",
    token_field_label="Twilio credential",
    token_placeholder="account_sid:auth_token",
    description="Connect Twilio for SMS/voice delivery diagnostics.",
    security_note="Store Account SID and Auth Token together or as a single API key.",
)

SENDGRID_CREDENTIAL_UI = cloud_credential_ui(
    label="SendGrid",
    token_field_label="SendGrid API key",
    token_placeholder="SG.…",
    description="Connect SendGrid for email delivery diagnostics.",
)

PAGERDUTY_CREDENTIAL_UI = cloud_credential_ui(
    label="PagerDuty",
    token_field_label="PagerDuty API token",
    description="Connect PagerDuty for incident and on-call diagnostics.",
)

SENTRY_CREDENTIAL_UI = cloud_credential_ui(
    label="Sentry",
    token_field_label="Sentry auth token",
    description="Connect Sentry for error tracking and release diagnostics.",
)

NEW_RELIC_CREDENTIAL_UI = cloud_credential_ui(
    label="New Relic",
    token_field_label="New Relic user API key",
    description="Connect New Relic for APM and observability diagnostics.",
)

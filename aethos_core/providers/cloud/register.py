# SPDX-License-Identifier: Apache-2.0
"""Register cloud and SaaS providers with vault-backed API token auth."""

from __future__ import annotations

from typing import Any

from aethos_core.providers.base.capability_matrix import OperationCapability, normalize_legacy_capability
from aethos_core.providers.base.credential_ui import (
    ANTHROPIC_CREDENTIAL_UI,
    AWS_CREDENTIAL_UI,
    AZURE_CREDENTIAL_UI,
    CLOUDFLARE_CREDENTIAL_UI,
    DATADOG_CREDENTIAL_UI,
    DIGITALOCEAN_CREDENTIAL_UI,
    FLY_CREDENTIAL_UI,
    GCP_CREDENTIAL_UI,
    HEROKU_CREDENTIAL_UI,
    MONGODB_ATLAS_CREDENTIAL_UI,
    NETLIFY_CREDENTIAL_UI,
    OPENAI_CREDENTIAL_UI,
    COHERE_CREDENTIAL_UI,
    DEEPSEEK_CREDENTIAL_UI,
    FIREWORKS_CREDENTIAL_UI,
    GEMINI_CREDENTIAL_UI,
    GROQ_CREDENTIAL_UI,
    MISTRAL_CREDENTIAL_UI,
    OPENROUTER_CREDENTIAL_UI,
    PERPLEXITY_CREDENTIAL_UI,
    TOGETHER_CREDENTIAL_UI,
    XAI_CREDENTIAL_UI,
    ORACLE_CLOUD_CREDENTIAL_UI,
    IBM_CLOUD_CREDENTIAL_UI,
    LINODE_CREDENTIAL_UI,
    SCALEWAY_CREDENTIAL_UI,
    HETZNER_CREDENTIAL_UI,
    TWILIO_CREDENTIAL_UI,
    SENDGRID_CREDENTIAL_UI,
    PAGERDUTY_CREDENTIAL_UI,
    SENTRY_CREDENTIAL_UI,
    NEW_RELIC_CREDENTIAL_UI,
    PLAID_CREDENTIAL_UI,
    RENDER_CREDENTIAL_UI,
    RESEND_CREDENTIAL_UI,
    STRIPE_CREDENTIAL_UI,
    SUPABASE_CREDENTIAL_UI,
    TAVILY_CREDENTIAL_UI,
    CredentialUiConfig,
)
from aethos_core.providers.base.provider_registry import ProviderRegistry, ProviderSpec
from aethos_core.providers.cloud.auth_adapter import ApiTokenAuthAdapter
from aethos_core.providers.cloud.validators import validate_cloud_provider_token

_READONLY_CAPABILITIES: dict[str, dict[str, Any]] = {
    "validate_identity": {"api": True, "enabled": True, "read_only": True},
}


def _capabilities() -> dict[str, OperationCapability]:
    return {op: normalize_legacy_capability(op, raw) for op, raw in _READONLY_CAPABILITIES.items()}


def _register_token_provider(
    *,
    name: str,
    label: str,
    category: str,
    credential_ui: CredentialUiConfig,
    missing_detail: str = "",
) -> ProviderSpec:
    existing = ProviderRegistry.get(name)
    if existing:
        return existing

    def _validate(token: str) -> dict[str, Any]:
        return validate_cloud_provider_token(name, token)

    spec = ProviderSpec(
        name=name,
        label=label,
        category=category,
        auth_adapter=ApiTokenAuthAdapter(
            provider=name,
            validate_fn=_validate,
            missing_detail=missing_detail or f"{label} credentials not configured — add a token in Mission Control → Advanced settings → Credentials.",
        ),
        capabilities=_capabilities(),
        mutation_adapter=None,
        credential_ui=credential_ui,
    )
    ProviderRegistry.register(spec)
    return spec


_CLOUD_PROVIDERS: list[tuple[str, str, str, CredentialUiConfig]] = [
    ("gcp", "GCP", "cloud", GCP_CREDENTIAL_UI),
    ("azure", "Azure", "cloud", AZURE_CREDENTIAL_UI),
    ("cloudflare", "Cloudflare", "cloud", CLOUDFLARE_CREDENTIAL_UI),
    ("digitalocean", "DigitalOcean", "cloud", DIGITALOCEAN_CREDENTIAL_UI),
    ("fly", "Fly.io", "cloud", FLY_CREDENTIAL_UI),
    ("render", "Render", "cloud", RENDER_CREDENTIAL_UI),
    ("netlify", "Netlify", "cloud", NETLIFY_CREDENTIAL_UI),
    ("heroku", "Heroku", "cloud", HEROKU_CREDENTIAL_UI),
    ("supabase", "Supabase", "cloud", SUPABASE_CREDENTIAL_UI),
    ("stripe", "Stripe", "payments", STRIPE_CREDENTIAL_UI),
    # §2 — model-API providers (grouped under "model" in Connections).
    ("openai", "OpenAI", "model", OPENAI_CREDENTIAL_UI),
    ("anthropic", "Anthropic", "model", ANTHROPIC_CREDENTIAL_UI),
    ("gemini", "Google Gemini", "model", GEMINI_CREDENTIAL_UI),
    ("mistral", "Mistral", "model", MISTRAL_CREDENTIAL_UI),
    ("groq", "Groq", "model", GROQ_CREDENTIAL_UI),
    ("xai", "xAI (Grok)", "model", XAI_CREDENTIAL_UI),
    ("deepseek", "DeepSeek", "model", DEEPSEEK_CREDENTIAL_UI),
    ("cohere", "Cohere", "model", COHERE_CREDENTIAL_UI),
    ("together", "Together", "model", TOGETHER_CREDENTIAL_UI),
    ("fireworks", "Fireworks", "model", FIREWORKS_CREDENTIAL_UI),
    ("perplexity", "Perplexity", "model", PERPLEXITY_CREDENTIAL_UI),
    ("openrouter", "OpenRouter", "model", OPENROUTER_CREDENTIAL_UI),
    ("tavily", "Tavily", "ai", TAVILY_CREDENTIAL_UI),
    ("resend", "Resend", "communications", RESEND_CREDENTIAL_UI),
    ("datadog", "Datadog", "observability", DATADOG_CREDENTIAL_UI),
    ("mongodb_atlas", "MongoDB Atlas", "database", MONGODB_ATLAS_CREDENTIAL_UI),
    ("plaid", "Plaid", "fintech", PLAID_CREDENTIAL_UI),
    ("oracle_cloud", "Oracle Cloud", "cloud", ORACLE_CLOUD_CREDENTIAL_UI),
    ("ibm_cloud", "IBM Cloud", "cloud", IBM_CLOUD_CREDENTIAL_UI),
    ("linode", "Linode (Akamai)", "cloud", LINODE_CREDENTIAL_UI),
    ("scaleway", "Scaleway", "cloud", SCALEWAY_CREDENTIAL_UI),
    ("hetzner", "Hetzner Cloud", "cloud", HETZNER_CREDENTIAL_UI),
    ("twilio", "Twilio", "communications", TWILIO_CREDENTIAL_UI),
    ("sendgrid", "SendGrid", "communications", SENDGRID_CREDENTIAL_UI),
    ("pagerduty", "PagerDuty", "observability", PAGERDUTY_CREDENTIAL_UI),
    ("sentry", "Sentry", "observability", SENTRY_CREDENTIAL_UI),
    ("new_relic", "New Relic", "observability", NEW_RELIC_CREDENTIAL_UI),
]


def register_cloud_providers() -> list[ProviderSpec]:
    specs = [_register_token_provider(name=n, label=l, category=c, credential_ui=ui) for n, l, c, ui in _CLOUD_PROVIDERS]
    return specs


def ensure_cloud_providers_registered() -> list[ProviderSpec]:
    return register_cloud_providers()

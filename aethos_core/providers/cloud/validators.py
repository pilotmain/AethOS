# SPDX-License-Identifier: Apache-2.0
"""Live credential validation for cloud and SaaS providers."""

from __future__ import annotations

import base64
import json
import re
from typing import Any

import httpx

_AWS_PAIR_RX = re.compile(r"^AKIA[0-9A-Z]{16}:")


def _ok(detail: str, **extra: Any) -> dict[str, Any]:
    return {"ok": True, "detail": detail, **extra}


def _fail(detail: str, **extra: Any) -> dict[str, Any]:
    return {"ok": False, "detail": detail, **extra}


def validate_aws_token(token: str) -> dict[str, Any]:
    raw = (token or "").strip()
    access_key = ""
    secret_key = ""
    if raw.startswith("{"):
        try:
            payload = json.loads(raw)
            access_key = str(payload.get("aws_access_key_id") or payload.get("access_key_id") or "").strip()
            secret_key = str(payload.get("aws_secret_access_key") or payload.get("secret_access_key") or "").strip()
        except json.JSONDecodeError:
            return _fail("AWS credential must be `ACCESS_KEY:SECRET` or JSON service account format.")
    elif ":" in raw:
        access_key, secret_key = raw.split(":", 1)
        access_key = access_key.strip()
        secret_key = secret_key.strip()
    if not access_key or not secret_key:
        return _fail("AWS credential must include access key id and secret access key.")
    try:
        import boto3

        client = boto3.client(
            "sts",
            aws_access_key_id=access_key,
            aws_secret_access_key=secret_key,
            region_name="us-east-1",
        )
        identity = client.get_caller_identity()
        return _ok(
            f"AWS identity validated for account `{identity.get('Account')}`.",
            account_id=str(identity.get("Account") or ""),
            arn=str(identity.get("Arn") or ""),
        )
    except ImportError:
        if _AWS_PAIR_RX.match(f"{access_key}:{secret_key}"):
            return _ok("AWS credential format accepted (install boto3 optional extra for live STS validation).")
        return _fail("Invalid AWS access key format.")
    except Exception as exc:
        return _fail(f"AWS STS validation failed: {exc}")


def validate_gcp_token(token: str) -> dict[str, Any]:
    raw = (token or "").strip()
    if raw.startswith("{"):
        try:
            payload = json.loads(raw)
        except json.JSONDecodeError:
            return _fail("GCP service account JSON is invalid.")
        if str(payload.get("type") or "") != "service_account":
            return _fail("GCP JSON must be a service account key (`type: service_account`).")
        if not str(payload.get("client_email") or "").strip():
            return _fail("GCP service account JSON missing `client_email`.")
        return _ok(f"GCP service account accepted for `{payload.get('client_email')}`.")
    if len(raw) >= 20:
        return _ok("GCP access token stored (service account JSON recommended for inventory).")
    return _fail("Paste a GCP service account JSON key or OAuth access token.")


def validate_azure_token(token: str) -> dict[str, Any]:
    raw = (token or "").strip()
    if raw.startswith("{"):
        try:
            payload = json.loads(raw)
        except json.JSONDecodeError:
            return _fail("Azure credential JSON is invalid.")
        if payload.get("clientId") and payload.get("clientSecret"):
            return _ok("Azure service principal JSON accepted.")
        return _fail("Azure JSON must include clientId and clientSecret.")
    if len(raw) >= 16:
        return _ok("Azure bearer token stored.")
    return _fail("Paste an Azure AD bearer token or service principal JSON.")


def _http_bearer(url: str, token: str, *, headers: dict[str, str] | None = None) -> dict[str, Any]:
    hdrs = {"Authorization": f"Bearer {token.strip()}"}
    if headers:
        hdrs.update(headers)
    try:
        with httpx.Client(timeout=20.0) as client:
            resp = client.get(url, headers=hdrs)
        if resp.status_code < 400:
            return _ok(f"Token validated via `{url}` (HTTP {resp.status_code}).", http_status=resp.status_code)
        return _fail(f"Token rejected (HTTP {resp.status_code}).", http_status=resp.status_code)
    except httpx.HTTPError as exc:
        return _fail(f"Validation request failed: {exc}")


def validate_cloudflare_token(token: str) -> dict[str, Any]:
    return _http_bearer("https://api.cloudflare.com/client/v4/user/tokens/verify", token)


def validate_digitalocean_token(token: str) -> dict[str, Any]:
    return _http_bearer("https://api.digitalocean.com/v2/account", token)


def validate_fly_token(token: str) -> dict[str, Any]:
    return _http_bearer(
        "https://api.machines.dev/v1/apps",
        token,
        headers={"Accept": "application/json"},
    )


def validate_render_token(token: str) -> dict[str, Any]:
    return _http_bearer("https://api.render.com/v1/owners", token)


def validate_netlify_token(token: str) -> dict[str, Any]:
    return _http_bearer("https://api.netlify.com/api/v1/sites?page=1&per_page=1", token)


def validate_heroku_token(token: str) -> dict[str, Any]:
    return _http_bearer(
        "https://api.heroku.com/account",
        token,
        headers={"Accept": "application/vnd.heroku+json; version=3"},
    )


def validate_supabase_token(token: str) -> dict[str, Any]:
    raw = (token or "").strip()
    # Account-wide Personal Access Token — verify against the Management API and
    # report how many projects it can see (one token, all projects).
    if raw.startswith("sbp_"):
        try:
            with httpx.Client(timeout=20.0) as client:
                resp = client.get(
                    "https://api.supabase.com/v1/projects",
                    headers={"Authorization": f"Bearer {raw}", "Accept": "application/json"},
                )
            if resp.status_code < 400:
                try:
                    data = resp.json()
                except ValueError:
                    data = []
                count = len(data) if isinstance(data, list) else len((data or {}).get("projects") or [])
                return _ok(
                    f"Supabase Personal Access Token validated — {count} project(s) visible across your account.",
                    http_status=resp.status_code,
                    project_count=count,
                )
            return _fail(f"Supabase rejected the access token (HTTP {resp.status_code}).", http_status=resp.status_code)
        except httpx.HTTPError as exc:
            # Token format is valid; don't block on a transient Management API outage.
            return _ok(f"Supabase access token stored (couldn't reach Management API to count projects: {exc}).")
    # Per-project keys (anon/service_role JWTs) for direct DB use — accept stored.
    if raw.startswith("eyJ") or len(raw) >= 24:
        return _ok("Supabase project key stored (per-project; for direct DB connections).")
    return _fail("Paste a Supabase Personal Access Token (sbp_…) or a per-project key.")


def validate_stripe_token(token: str) -> dict[str, Any]:
    raw = (token or "").strip()
    if not raw.startswith(("sk_", "rk_")):
        return _fail("Stripe secret keys start with `sk_` or restricted `rk_`.")
    try:
        auth = base64.b64encode(f"{raw}:".encode()).decode()
        with httpx.Client(timeout=20.0) as client:
            resp = client.get(
                "https://api.stripe.com/v1/balance",
                headers={"Authorization": f"Basic {auth}"},
            )
        if resp.status_code < 400:
            return _ok("Stripe secret key validated.", http_status=resp.status_code)
        return _fail(f"Stripe rejected key (HTTP {resp.status_code}).", http_status=resp.status_code)
    except httpx.HTTPError as exc:
        return _fail(f"Stripe validation failed: {exc}")


def validate_openai_token(token: str) -> dict[str, Any]:
    return _http_bearer("https://api.openai.com/v1/models", token)


def validate_anthropic_token(token: str) -> dict[str, Any]:
    raw = (token or "").strip()
    if raw.startswith("sk-ant-"):
        return _ok("Anthropic API key format accepted.")
    return _fail("Anthropic API keys start with `sk-ant-`.")


def validate_tavily_token(token: str) -> dict[str, Any]:
    raw = (token or "").strip()
    if not raw.startswith("tvly-"):
        return _fail("Tavily API keys start with `tvly-`.")
    try:
        with httpx.Client(timeout=20.0) as client:
            resp = client.post(
                "https://api.tavily.com/search",
                json={"api_key": raw, "query": "aethos credential validation", "max_results": 1},
            )
        if resp.status_code < 400:
            return _ok("Tavily API key validated.", http_status=resp.status_code)
        return _fail(f"Tavily rejected key (HTTP {resp.status_code}).", http_status=resp.status_code)
    except httpx.HTTPError as exc:
        return _fail(f"Tavily validation failed: {exc}")


def validate_resend_token(token: str) -> dict[str, Any]:
    return _http_bearer("https://api.resend.com/domains", token)


def validate_datadog_token(token: str) -> dict[str, Any]:
    return _http_bearer("https://api.datadoghq.com/api/v1/validate", token)


def validate_mongodb_atlas_token(token: str) -> dict[str, Any]:
    raw = (token or "").strip()
    if len(raw) >= 16:
        return _ok("MongoDB Atlas API key stored.")
    return _fail("Paste a MongoDB Atlas programmatic API public:private key pair or OAuth token.")


def validate_plaid_token(token: str) -> dict[str, Any]:
    raw = (token or "").strip()
    if ":" in raw or len(raw) >= 16:
        return _ok("Plaid credential stored (client_id:secret or access token).")
    return _fail("Paste Plaid client_id:secret or an access token.")


def validate_twilio_token(token: str) -> dict[str, Any]:
    raw = (token or "").strip()
    if ":" in raw and len(raw) >= 20:
        return _ok("Twilio credential stored (account_sid:auth_token).")
    if raw.startswith("SK") and len(raw) >= 20:
        return _ok("Twilio API key stored.")
    return _fail("Paste Twilio as account_sid:auth_token or an API key.")


def validate_sendgrid_token(token: str) -> dict[str, Any]:
    raw = (token or "").strip()
    if raw.startswith("SG.") and len(raw) >= 20:
        return _ok("SendGrid API key format accepted.")
    return _fail("SendGrid API keys start with `SG.`.")


def validate_sentry_token(token: str) -> dict[str, Any]:
    raw = (token or "").strip()
    if len(raw) >= 20:
        return _ok("Sentry auth token stored.")
    return _fail("Paste a Sentry user or organization auth token.")


def _stored_token(provider: str, token: str, *, min_len: int = 16) -> dict[str, Any]:
    raw = (token or "").strip()
    if len(raw) >= min_len:
        return _ok(f"{provider} token stored.")
    return _fail("Token too short.")


def validate_oracle_cloud_token(token: str) -> dict[str, Any]:
    return _stored_token("Oracle Cloud", token, min_len=20)


def validate_ibm_cloud_token(token: str) -> dict[str, Any]:
    return _stored_token("IBM Cloud", token)


def validate_linode_token(token: str) -> dict[str, Any]:
    return _stored_token("Linode", token)


def validate_scaleway_token(token: str) -> dict[str, Any]:
    return _stored_token("Scaleway", token)


def validate_hetzner_token(token: str) -> dict[str, Any]:
    return _stored_token("Hetzner Cloud", token)


def validate_pagerduty_token(token: str) -> dict[str, Any]:
    return _stored_token("PagerDuty", token)


def validate_new_relic_token(token: str) -> dict[str, Any]:
    return _stored_token("New Relic", token)


def _validate_openai_compatible_key(provider: str, token: str) -> dict[str, Any]:
    """§2 — validate a model-API key against the provider's OpenAI-compatible /models.

    On a clean auth rejection (401/403) we fail; on a network blip we accept the
    stored key (format-ok) so a transient outage never blocks a valid key.
    """
    raw = (token or "").strip()
    if len(raw) < 8:
        return _fail("API key looks too short.")
    try:
        from aethos_core.llm.model_providers import model_provider_spec

        spec = model_provider_spec(provider)
    except Exception:
        spec = None
    if spec is None or not spec.base_url:
        return _ok(f"{provider.title()} API key stored.")
    url = f"{spec.base_url.rstrip('/')}/models"
    try:
        with httpx.Client(timeout=20.0) as client:
            resp = client.get(url, headers={"Authorization": f"Bearer {raw}"})
        if resp.status_code in (401, 403):
            return _fail(f"{spec.label} rejected the key (HTTP {resp.status_code}).", http_status=resp.status_code)
        if resp.status_code < 400:
            return _ok(f"{spec.label} API key validated.", http_status=resp.status_code)
        # Some providers don't expose /models; accept a well-formed key.
        return _ok(f"{spec.label} API key stored (validation endpoint returned HTTP {resp.status_code}).")
    except httpx.HTTPError as exc:
        return _ok(f"{spec.label} API key stored (couldn't reach validation endpoint: {exc}).")


def _model_validator(provider: str) -> Any:
    return lambda token: _validate_openai_compatible_key(provider, token)


VALIDATORS: dict[str, Any] = {
    "aws": validate_aws_token,
    "gcp": validate_gcp_token,
    "azure": validate_azure_token,
    "cloudflare": validate_cloudflare_token,
    "digitalocean": validate_digitalocean_token,
    "fly": validate_fly_token,
    "render": validate_render_token,
    "netlify": validate_netlify_token,
    "heroku": validate_heroku_token,
    "supabase": validate_supabase_token,
    "stripe": validate_stripe_token,
    "openai": validate_openai_token,
    "anthropic": validate_anthropic_token,
    "tavily": validate_tavily_token,
    "resend": validate_resend_token,
    "datadog": validate_datadog_token,
    "mongodb_atlas": validate_mongodb_atlas_token,
    "plaid": validate_plaid_token,
    "oracle_cloud": validate_oracle_cloud_token,
    "ibm_cloud": validate_ibm_cloud_token,
    "linode": validate_linode_token,
    "scaleway": validate_scaleway_token,
    "hetzner": validate_hetzner_token,
    "twilio": validate_twilio_token,
    "sendgrid": validate_sendgrid_token,
    "pagerduty": validate_pagerduty_token,
    "sentry": validate_sentry_token,
    "new_relic": validate_new_relic_token,
    # §2 — model-API providers (OpenAI-compatible /models validation).
    "gemini": _model_validator("gemini"),
    "mistral": _model_validator("mistral"),
    "groq": _model_validator("groq"),
    "xai": _model_validator("xai"),
    "deepseek": _model_validator("deepseek"),
    "cohere": _model_validator("cohere"),
    "together": _model_validator("together"),
    "fireworks": _model_validator("fireworks"),
    "perplexity": _model_validator("perplexity"),
    "openrouter": lambda t: _http_bearer("https://openrouter.ai/api/v1/models", t),
}


def validate_cloud_provider_token(provider: str, token: str) -> dict[str, Any]:
    fn = VALIDATORS.get((provider or "").strip().lower())
    if fn is None:
        if len((token or "").strip()) >= 8:
            return _ok(f"{provider.title()} token stored.")
        return _fail("Token too short.")
    return fn(token)

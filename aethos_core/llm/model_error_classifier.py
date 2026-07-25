# SPDX-License-Identifier: Apache-2.0
"""Classify model-provider call failures into honest, user-facing categories.

Distinguishes AethOS-side config problems (no key) from the user's provider
account problems (402 needs billing, 429 rate-limited/quota) and transient
provider outages (5xx/timeout). The key *worked* on a 402/429 — the account just
lacks credits/quota — so we must not present those as AethOS bugs.
"""

from __future__ import annotations

# category -> (short label, friendly hint, side)
#   side: "config" = AethOS/Connections; "account" = user's provider billing;
#         "transient" = retry; "error" = unknown.
CATEGORY_NOT_CONFIGURED = "not_configured"
CATEGORY_AUTH = "auth"
CATEGORY_BILLING = "account_billing"
CATEGORY_RATE_LIMIT = "rate_limited"
CATEGORY_UNAVAILABLE = "unavailable"
CATEGORY_ERROR = "error"


def classify_status(status_code: int | None, *, provider_label: str = "The provider") -> dict[str, str]:
    """Classify by HTTP status code."""
    if status_code in (401, 403):
        return {
            "category": CATEGORY_AUTH,
            "side": "config",
            "message": f"{provider_label}: key rejected — re-add it in Mission Control → Advanced settings → Credentials.",
        }
    if status_code == 402:
        return {
            "category": CATEGORY_BILLING,
            "side": "account",
            "message": f"{provider_label} account needs credits/billing — add credits in your provider account.",
        }
    if status_code == 429:
        return {
            "category": CATEGORY_RATE_LIMIT,
            "side": "account",
            "message": f"{provider_label}: rate-limited / quota exceeded — check your provider billing & limits.",
        }
    if status_code is not None and 500 <= status_code < 600:
        return {
            "category": CATEGORY_UNAVAILABLE,
            "side": "transient",
            "message": f"{provider_label} temporarily unavailable (HTTP {status_code}) — retry.",
        }
    return {
        "category": CATEGORY_ERROR,
        "side": "error",
        "message": f"{provider_label} request failed (HTTP {status_code}).",
    }


def classify_text(text: str | None, *, provider_label: str = "The provider") -> dict[str, str]:
    """Best-effort classification from an error string (no status available)."""
    low = (text or "").lower()
    if "not configured" in low or "add a key" in low:
        return {
            "category": CATEGORY_NOT_CONFIGURED,
            "side": "config",
            "message": f"{provider_label}: not configured — add a key in Mission Control → Advanced settings → Credentials.",
        }
    if "402" in low or "payment required" in low or "insufficient" in low or "credit" in low:
        return classify_status(402, provider_label=provider_label)
    if "429" in low or "too many requests" in low or "rate limit" in low or "quota" in low:
        return classify_status(429, provider_label=provider_label)
    if "401" in low or "403" in low or "unauthorized" in low or "forbidden" in low or "invalid api key" in low:
        return classify_status(401, provider_label=provider_label)
    if "timeout" in low or "timed out" in low or "unavailable" in low or "connection" in low:
        return {
            "category": CATEGORY_UNAVAILABLE,
            "side": "transient",
            "message": f"{provider_label} temporarily unavailable — retry.",
        }
    return {"category": CATEGORY_ERROR, "side": "error", "message": (text or "Request failed.")}

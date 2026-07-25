# SPDX-License-Identifier: Apache-2.0
"""Vercel / Next.js build-time env criticality — blocks deploy when app cannot build."""

from __future__ import annotations

from aethos_core.providers.railway.env_value_readiness.env_classification import (
    EnvCriticality,
    classify_env_var,
    is_secret_env_name,
)


def list_build_critical_env_names(
    names: list[str],
    *,
    framework: str = "",
) -> list[str]:
    """Env vars required before a Vercel deploy is worth attempting."""
    fw = (framework or "").strip().lower()
    out: list[str] = []
    for raw in names:
        name = str(raw or "").strip()
        if not name:
            continue
        upper = name.upper()
        if fw in {"nextjs", "next"} and upper.startswith("NEXT_PUBLIC_"):
            out.append(name)
            continue
        if is_secret_env_name(upper) or classify_env_var(upper) == EnvCriticality.CRITICAL_SECRET:
            out.append(name)
            continue
        if any(token in upper for token in ("SUPABASE", "STRIPE", "PLAID", "DATABASE_URL", "CLERK", "AUTH0")):
            out.append(name)
    return sorted({n.upper(): n for n in out}.values(), key=str.upper)


def infer_env_integration(name: str) -> str:
    upper = (name or "").strip().upper()
    if "SUPABASE" in upper:
        return "supabase"
    if "STRIPE" in upper:
        return "stripe"
    if "PLAID" in upper:
        return "plaid"
    if "RESEND" in upper:
        return "resend"
    if "CLERK" in upper:
        return "clerk"
    if "AUTH0" in upper:
        return "auth0"
    if "ANTHROPIC" in upper:
        return "anthropic"
    if "OPENAI" in upper:
        return "openai"
    if "GITHUB" in upper:
        return "github"
    if "VERCEL" in upper:
        return "vercel"
    return "app"

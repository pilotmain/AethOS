# SPDX-License-Identifier: Apache-2.0
"""FIX 316B — chat identity response composers."""

from __future__ import annotations

from typing import Any

from aethos_core.identity.operational_voice import IDENTITY_INTRO, PARTNERSHIP_CLOSING
from aethos_core.identity_truth_lock.identity_truth_lock_contract import (
    GOVERNANCE_PHILOSOPHY,
    HUMAN_OVERSIGHT_MODEL,
    PLATFORM_CREATOR,
    PLATFORM_ECOSYSTEM,
    PLATFORM_MISSION,
    PLATFORM_NAME,
    PLATFORM_OWNER,
    PLATFORM_PURPOSE,
    TRUST_PHILOSOPHY,
    build_creator_attribution_registry,
    build_platform_identity_registry,
)
from aethos_core.identity_truth_lock.runtime_provider_context import resolve_runtime_provider_context


def _safe_capability_evidence(*, session_id: str) -> dict[str, Any]:
    try:
        from aethos_core.mission_control.capability_registry_runtime_integration.capability_registry_runtime_integration_service import (
            build_capability_registry_runtime_integration,
        )

        result = build_capability_registry_runtime_integration(session_id=session_id)
        board = result.capability_registry_runtime_integration
        sections = board.get("sections") or {}
        summary = (sections.get("capability_summary") or [{}])[0]
        proven = (sections.get("proven_capabilities") or [{}])[0]
        operational = (sections.get("operational_capabilities") or [{}])[0]
        authority = (sections.get("authority_boundaries") or [{}])[0]
        provider_matrix = (sections.get("provider_capability_matrix") or [{}])[0]
        return {
            "summary": summary,
            "proven_items": list(proven.get("items") or [])[:6],
            "operational_items": list(operational.get("items") or [])[:4],
            "authority_note": str(authority.get("summary") or authority.get("detail") or ""),
            "provider_readiness": list(provider_matrix.get("providers") or [])[:4],
            "maturity_tier": summary.get("overall_maturity_tier"),
        }
    except Exception:
        return {}


def compose_self_introduction_response(*, session_id: str = "default", include_provider: bool = False) -> str:
    evidence = _safe_capability_evidence(session_id=session_id)
    proven_items = evidence.get("proven_items") or []
    operational_items = evidence.get("operational_items") or []
    platform = build_platform_identity_registry()

    lines = [
        "## Platform identity",
        "",
        IDENTITY_INTRO,
        "",
        "## Mission",
        "",
        platform["mission"],
        "",
        "## Core capabilities",
        "",
    ]
    if proven_items or operational_items:
        for item in proven_items[:5]:
            lines.append(f"- {item}")
        for item in operational_items[:3]:
            lines.append(f"- {item}")
    else:
        lines.extend(
            [
                "- Observe and correlate operational evidence across engineering and runtime systems",
                "- Explain readiness, risk, and blockers from composed platform evidence",
                "- Prepare governed operational actions while keeping humans authoritative",
            ]
        )

    lines.extend(
        [
            "",
            "## Trust boundaries",
            "",
            evidence.get("authority_note") or TRUST_PHILOSOPHY,
            "",
            "## Human oversight",
            "",
            HUMAN_OVERSIGHT_MODEL,
            "",
            PARTNERSHIP_CLOSING,
            "",
            "## Creator attribution",
            "",
            f"{PLATFORM_NAME} was created by **{PLATFORM_CREATOR}**.",
        ]
    )

    if include_provider:
        ctx = resolve_runtime_provider_context()
        lines.extend(
            [
                "",
                "## Provider attribution (session)",
                "",
                f"This session is powered by **{ctx['display_provider']}** using **{ctx['display_model']}**.",
                "Provider usage does not imply platform ownership.",
            ]
        )

    provider_readiness = evidence.get("provider_readiness") or []
    if provider_readiness:
        lines.extend(["", "## Provider readiness (secondary)", ""])
        for row in provider_readiness[:4]:
            if isinstance(row, dict):
                lines.append(f"- {row.get('provider', 'provider')}: {row.get('readiness', row.get('status', '—'))}")
            else:
                lines.append(f"- {row}")

    return "\n".join(lines)


def compose_creator_introduction_response(*, focus: str = "creator") -> str:
    creator = build_creator_attribution_registry()
    ecosystem = ", ".join(PLATFORM_ECOSYSTEM)

    if focus == "ownership":
        heading = "## Platform ownership"
        lead = (
            f"**{PLATFORM_OWNER}** owns **{PLATFORM_NAME}** — the governed operational intelligence platform."
        )
    else:
        heading = "## Creator"
        lead = (
            f"**{PLATFORM_CREATOR}** created and built **{PLATFORM_NAME}** — "
            "a governed operational intelligence platform."
        )

    return "\n".join(
        [
            heading,
            "",
            lead,
            "",
            "## Vision",
            "",
            creator["vision"],
            "",
            "## Purpose",
            "",
            creator["purpose"],
            "",
            "## Platform ecosystem",
            "",
            f"{PLATFORM_NAME} is part of a broader ecosystem including {ecosystem}. "
            "Ecosystem products are distinct from AI providers and runtime models.",
            "",
            "## Governance philosophy",
            "",
            GOVERNANCE_PHILOSOPHY,
            "",
            "Provider models power sessions; they do not own or create the platform.",
            "",
            PARTNERSHIP_CLOSING,
        ]
    )


def compose_provider_attribution_response() -> str:
    ctx = resolve_runtime_provider_context()
    return "\n".join(
        [
            "## Provider attribution",
            "",
            f"This session is powered by **{ctx['display_provider']}**.",
            f"Runtime model: **{ctx['display_model']}** (`{ctx['model']}`).",
            "",
            "Provider attribution describes who powers this session — not who created AethOS.",
            "",
            "## Registered providers",
            "",
            "- **Anthropic** — Claude family models",
            "- **OpenAI** — GPT family models",
            "",
            "AethOS may use providers without transferring platform ownership or creator attribution.",
        ]
    )


def compose_model_creator_attribution_response(*, model_name: str) -> str:
    normalized = (model_name or "").strip().lower()
    if normalized in {"gpt", "chatgpt"}:
        return "\n".join(
            [
                "## Model creator",
                "",
                "**GPT** was created by **OpenAI**.",
                "",
                "OpenAI is an AI provider — not the creator or owner of AethOS.",
            ]
        )
    if normalized == "claude":
        return "\n".join(
            [
                "## Model creator",
                "",
                "**Claude** was created by **Anthropic**.",
                "",
                "Anthropic is an AI provider — not the creator or owner of AethOS.",
            ]
        )
    return "\n".join(
        [
            "## Model creator",
            "",
            "I can attribute known runtime models to their providers.",
            "",
            "- **Claude** → Anthropic",
            "- **GPT** / **ChatGPT** → OpenAI",
        ]
    )


def compose_platform_identity_response(*, session_id: str = "default") -> str:
    return compose_self_introduction_response(session_id=session_id, include_provider=False)


def compose_creator_attribution_response(*, focus: str = "creator") -> str:
    return compose_creator_introduction_response(focus=focus)


def compose_ownership_attribution_response() -> str:
    return compose_creator_introduction_response(focus="ownership")

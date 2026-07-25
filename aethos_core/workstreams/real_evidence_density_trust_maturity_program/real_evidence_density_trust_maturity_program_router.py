# SPDX-License-Identifier: Apache-2.0
"""WORKSTREAM_G1 / FIX 354 — chat router."""

from __future__ import annotations

from aethos_core.workstreams.real_evidence_density_trust_maturity_program.real_evidence_density_trust_maturity_program_contract import (
    AUTHORITY_EXPANSION_FIX_354,
    AUTOMATIC_EVIDENCE_ACCEPTANCE_FIX_354,
    CUSTOMER_MANIPULATION_FIX_354,
    GOVERNANCE_BYPASS_AUTHORITY_FIX_354,
    GOVERNANCE_MUTATION_FIX_354,
    LOCAL_EVIDENCE_MATURITY_EXECUTABLE_FIX_354,
    MUTATION_PERFORMED_FIX_354,
    PROVIDER_MUTATION_FIX_354,
    REAL_EVIDENCE_DENSITY_TRUST_MATURITY_PROGRAM_ROUTE_ID,
    TRUST_AUTHORITY_FIX_354,
    TRUST_MUTATION_AUTHORITY_FIX_354,
    TRUST_PROMOTION_FIX_354,
)
from aethos_core.workstreams.real_evidence_density_trust_maturity_program.real_evidence_density_trust_maturity_program_intent import (
    handle_evidence_maturity_intent,
    parse_evidence_maturity_intent,
)
from aethos_core.workstreams.real_evidence_density_trust_maturity_program.real_evidence_density_trust_maturity_program_renderer import (
    render_real_evidence_density_trust_maturity_program,
)
from aethos_core.workstreams.real_evidence_density_trust_maturity_program.real_evidence_density_trust_maturity_program_service import (
    build_real_evidence_density_trust_maturity_program,
)


def _meta(session_id: str, *, stage: str, **extra: str) -> dict[str, str]:
    return {
        "route_id": REAL_EVIDENCE_DENSITY_TRUST_MATURITY_PROGRAM_ROUTE_ID,
        "matched_module": (
            "workstreams.real_evidence_density_trust_maturity_program."
            "real_evidence_density_trust_maturity_program_router"
        ),
        "session_id": session_id,
        "readonly": "true",
        "mutation_performed": "false" if MUTATION_PERFORMED_FIX_354 is False else "true",
        "trust_authority": "false" if TRUST_AUTHORITY_FIX_354 is False else "true",
        "trust_promotion": "false" if TRUST_PROMOTION_FIX_354 is False else "true",
        "automatic_evidence_acceptance": "false"
        if AUTOMATIC_EVIDENCE_ACCEPTANCE_FIX_354 is False
        else "true",
        "customer_manipulation": "false" if CUSTOMER_MANIPULATION_FIX_354 is False else "true",
        "provider_mutation": "false" if PROVIDER_MUTATION_FIX_354 is False else "true",
        "governance_mutation": "false" if GOVERNANCE_MUTATION_FIX_354 is False else "true",
        "authority_expansion": "false" if AUTHORITY_EXPANSION_FIX_354 is False else "true",
        "governance_bypass_authority": "false" if GOVERNANCE_BYPASS_AUTHORITY_FIX_354 is False else "true",
        "trust_mutation_authority": "false" if TRUST_MUTATION_AUTHORITY_FIX_354 is False else "true",
        "local_evidence_maturity_executable": "true"
        if LOCAL_EVIDENCE_MATURITY_EXECUTABLE_FIX_354 is True
        else "false",
        "mutation_scope": "real_evidence_density_trust_maturity_program",
        "presentation_bypass": "true",
        "presentation_mode": "engineering",
        "suppress_governance_footer": "true",
        "mission_control_stage": stage,
        "lane_separation": "evidence_density_not_trust_authority",
        **extra,
    }


def route_real_evidence_density_trust_maturity_program(
    text: str,
    *,
    session_id: str = "default",
) -> tuple[str, str, dict[str, str]] | None:
    intent = parse_evidence_maturity_intent(text)
    if intent is None:
        return None

    sid = (session_id or "default").strip()[:64] or "default"
    handled = handle_evidence_maturity_intent(intent, session_id=sid)

    if handled.get("action") == "domain":
        entry = handled.get("entry") or {}
        body = (
            f"Evidence domain **{entry.get('domain_id')}** registered "
            f"(source={entry.get('source')}). "
            "Evidence density ≠ trust authority."
        )
        return (
            body,
            "workstream_real_evidence_density_trust_maturity_program_domain",
            _meta(sid, stage="domain"),
        )

    if handled.get("action") == "record":
        record = handled.get("record") or {}
        body = (
            f"Evidence maturity note recorded ({record.get('kind', 'note')}). "
            "Validation measures confidence — no trust promotion or authority change."
        )
        return (
            body,
            "workstream_real_evidence_density_trust_maturity_program_record",
            _meta(sid, stage="record", record_kind=str(record.get("kind") or "")),
        )

    focus = str(handled.get("focus") or "evidence_maturity_dashboard")
    result = build_real_evidence_density_trust_maturity_program(session_id=sid)
    markdown = render_real_evidence_density_trust_maturity_program(
        result.real_evidence_density_trust_maturity_program,
        focus=focus,
    )
    metrics = result.real_evidence_density_trust_maturity_program.get("metrics") or {}
    headline = (
        f"Density **{metrics.get('evidence_density_score')}** · "
        f"Freshness **{metrics.get('evidence_freshness_score')}** · "
        f"Trust maturity **{metrics.get('trust_maturity_score')}**."
    )
    body = f"{headline}\n\n{markdown}"
    return (
        body,
        "workstream_real_evidence_density_trust_maturity_program",
        _meta(sid, stage="view", focus=focus),
    )

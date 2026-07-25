# SPDX-License-Identifier: Apache-2.0
"""FIX 119 — production verification diagnostics router."""

from __future__ import annotations

import re

from aethos_core.providers.railway.execution_contract.execution_context import (
    resolve_execution_id_for_plan,
)
from aethos_core.providers.railway.execution_contract.production_policy import (
    assess_railway_production_policy,
)
from aethos_core.providers.railway.execution_contract.production_shadow_journal import (
    load_shadow_journal,
)
from aethos_core.providers.railway.execution_contract.production_verification_evidence import (
    collect_shadow_verification_evidence,
)
from aethos_core.providers.railway.execution_contract.production_verification_receipts import (
    load_verification_receipt,
)
from aethos_core.providers.railway.execution_contract.production_verification_renderer import (
    render_production_verification_evidence_report,
    render_production_verification_readiness,
)
from aethos_core.providers.railway.execution_contract.production_verification_rules import (
    assess_production_verification_evidence,
)
from aethos_core.providers.railway.execution_contract.production_verification_service import (
    assess_production_verification_readiness,
    run_production_shadow_runtime_verification,
)

_EVIDENCE_RX = re.compile(r"\bshow\s+railway\s+production\s+verification\s+evidence\b", re.I)
_READINESS_RX = re.compile(r"\bshow\s+railway\s+production\s+verification\s+readiness\b", re.I)
_ROLLBACK_REC_RX = re.compile(
    r"\bshow\s+railway\s+production\s+rollback\s+recommendation\b",
    re.I,
)


def is_railway_production_verification_intent(text: str) -> bool:
    raw = (text or "").strip()
    return bool(_EVIDENCE_RX.search(raw) or _READINESS_RX.search(raw) or _ROLLBACK_REC_RX.search(raw))


def _meta(session_id: str, *, stage: str, **extra: str) -> dict[str, str]:
    return {
        "route_id": "railway_production_verification",
        "matched_module": "providers.railway.execution_contract.production_verification_router",
        "session_id": session_id,
        "readonly": "true",
        "mutation_performed": "false",
        "presentation_bypass": "true",
        "presentation_mode": "engineering",
        "suppress_governance_footer": "true",
        "production_verification_stage": stage,
        **extra,
    }


def route_railway_production_verification(
    text: str,
    *,
    session_id: str = "default",
) -> tuple[str, str, dict[str, str]] | None:
    raw = (text or "").strip()
    if not is_railway_production_verification_intent(raw):
        return None

    from aethos_core.providers.railway.deployment_lifecycle.deployment_lifecycle_session_hydration import (
        ensure_railway_deployment_lifecycle_for_lane,
    )

    lane = ensure_railway_deployment_lifecycle_for_lane(
        session_id=session_id,
        user_text=raw,
        require_plan=True,
    )
    plan = lane.plan or {}
    execution_id = resolve_execution_id_for_plan(session_id=session_id, plan=plan) if plan else ""
    shadow_journal = load_shadow_journal(execution_id=execution_id) if execution_id else None

    if _READINESS_RX.search(raw):
        readiness = assess_production_verification_readiness(
            plan=plan,
            execution_id=execution_id,
            shadow_journal=shadow_journal,
        )
        body = render_production_verification_readiness(readiness=readiness)
        return body, "railway_production_verification_readiness", _meta(
            session_id,
            stage="readiness",
            ready=str(readiness.get("ready")).lower(),
        )

    if _ROLLBACK_REC_RX.search(raw):
        receipt = load_verification_receipt(execution_id=execution_id) if execution_id else None
        assessment_data = (receipt or {}).get("assessment") or {}
        if shadow_journal and isinstance(shadow_journal.get("production_verification"), dict):
            assessment_data = shadow_journal["production_verification"].get("assessment") or assessment_data
        rec = str(assessment_data.get("rollback_recommendation") or "blocked_pending_evidence")
        esc = str(assessment_data.get("incident_escalation") or "none")
        body = "\n".join(
            [
                "# Railway Production Rollback Recommendation",
                "",
                f"- rollback_recommendation: **{rec}**",
                f"- incident_escalation: **{esc}**",
                "",
                "Autonomous production rollback is prohibited. Follow manual escalation policy.",
                "",
                "No Railway mutation has been performed.",
            ]
        )
        return body, "railway_production_rollback_recommendation", _meta(
            session_id,
            stage="rollback_recommendation",
            recommendation=rec,
        )

    if _EVIDENCE_RX.search(raw):
        if execution_id and shadow_journal:
            result = run_production_shadow_runtime_verification(
                execution_id=execution_id,
                plan=plan,
                shadow_journal=shadow_journal,
            )
            body = render_production_verification_evidence_report(
                evidence=result.evidence,
                assessment=result.assessment,
                receipt=result.receipt,
            )
            return body, "railway_production_verification_evidence", _meta(
                session_id,
                stage="evidence",
                verification_passed=str(result.verification_passed).lower(),
            )

        bundle = collect_shadow_verification_evidence(
            execution_id=execution_id or "—",
            plan=plan,
            shadow_journal=shadow_journal,
        )
        policy = assess_railway_production_policy(plan=plan, execution_id=execution_id)
        assessment = assess_production_verification_evidence(
            bundle,
            incident_mode_active=policy.incident_mode_active,
        )
        body = render_production_verification_evidence_report(
            evidence=bundle,
            assessment=assessment,
        )
        return body, "railway_production_verification_evidence", _meta(
            session_id,
            stage="evidence_preview",
            verification_passed=str(assessment.verification_passed).lower(),
        )

    return None

# SPDX-License-Identifier: Apache-2.0
"""FIX 316C — evidence-backed public responses."""

from __future__ import annotations

from aethos_core.truth_consistency.truth_consistency_evidence import collect_truth_evidence_lightweight


def compose_provider_support_response(*, session_id: str = "default") -> str:
    from aethos_core.mission_control.provider_connection_experience.provider_connection_experience_contract import (
        PHASE_1_PROVIDERS,
        PHASE_2_PROVIDERS,
    )

    evidence = collect_truth_evidence_lightweight(session_id=session_id)
    report = evidence.get("provider_summary") or {}
    phase_1 = report.get("phase_1_providers") or list(PHASE_1_PROVIDERS)
    phase_2 = report.get("phase_2_providers") or list(PHASE_2_PROVIDERS)

    lines = [
        "## Provider support",
        "",
        "I answer from FIX 303 provider connection evidence composed with FIX 295 capability matrix data.",
        "",
        "### Phase 1 (connection flows available)",
        "",
    ]
    for provider in phase_1:
        lines.append(f"- **{provider}** — read-only inspection and approval-gated connection preparation")
    lines.extend(
        [
            "",
            "### Phase 2 (planned)",
            "",
        ]
    )
    for provider in phase_2:
        lines.append(f"- **{provider}** — planned; not certified as fully operational")
    lines.extend(
        [
            "",
            "### Limitations",
            "",
            "- Provider connection remains read-only and human-authoritative.",
            "- Secret collection in chat is forbidden.",
            "- Provider usage does not imply platform ownership.",
        ]
    )
    return "\n".join(lines)


def compose_launch_readiness_response(*, session_id: str = "default") -> str:
    sid = (session_id or "default").strip()[:64] or "default"
    evidence = collect_truth_evidence_lightweight(session_id=sid)
    readiness = dict(evidence.get("readiness_summary") or {})

    if str(readiness.get("overall_launch_status") or "UNKNOWN") == "UNKNOWN":
        try:
            from aethos_core.mission_control.saas_launch_readiness_assessment.saas_launch_readiness_assessment_service import (
                build_saas_launch_readiness_assessment,
            )

            launch309 = build_saas_launch_readiness_assessment(session_id=sid).saas_launch_readiness_assessment or {}
            readiness["overall_launch_status"] = launch309.get("overall_launch_status") or readiness.get(
                "overall_launch_status"
            )
            readiness["blockers"] = list(launch309.get("blockers") or [])[:6]
        except Exception:
            pass

        try:
            from aethos_core.mission_control.public_launch_readiness_freeze.public_launch_readiness_freeze_service import (
                build_public_launch_readiness_freeze,
            )

            launch314 = build_public_launch_readiness_freeze(session_id=sid).public_launch_readiness_freeze or {}
            readiness["overall_launch_status"] = launch314.get("overall_launch_status") or readiness.get(
                "overall_launch_status"
            )
            readiness["launch_recommendation_freeze"] = launch314.get("launch_recommendation_freeze")
        except Exception:
            pass

        try:
            from aethos_core.mission_control.launch_decision_package.launch_decision_package_service import (
                build_launch_decision_package,
            )

            launch315 = build_launch_decision_package(session_id=sid).launch_decision_package or {}
            readiness["launch_recommendation_package"] = launch315.get("launch_recommendation_package")
        except Exception:
            pass

    status = str(readiness.get("overall_launch_status") or "UNKNOWN")
    freeze = readiness.get("launch_recommendation_freeze")
    package = readiness.get("launch_recommendation_package")
    blockers = list(readiness.get("blockers") or [])

    lines = [
        "## Launch readiness",
        "",
        "This answer is composed from FIX 309, FIX 314, and FIX 315 evidence — not model priors.",
        "",
        f"Overall launch status: **{status}**",
    ]
    if freeze:
        lines.append(f"Launch recommendation freeze (FIX 314): **{freeze}**")
    if package:
        lines.append(f"Launch decision package recommendation (FIX 315): **{package}**")
    if blockers:
        lines.extend(["", "### Blockers", ""])
        for blocker in blockers[:6]:
            lines.append(f"- {blocker}")
    lines.extend(
        [
            "",
            "### Truth boundary",
            "",
            "Launch readiness is evidence-derived and human-authoritative. "
            "AethOS does not self-approve launch or mutate trust states.",
        ]
    )
    return "\n".join(lines)

# SPDX-License-Identifier: Apache-2.0
"""FIX 316C — composed platform evidence for truth validation."""

from __future__ import annotations

from typing import Any


def _section_items(payload: dict[str, Any], section: str, key: str = "items") -> list[str]:
    sections = payload.get("sections") or {}
    block = (sections.get(section) or [{}])[0]
    return [str(item) for item in (block.get(key) or [])]


def _safe_call(name: str, builder, *, session_id: str) -> tuple[Any, bool]:
    try:
        return builder(session_id=session_id), True
    except Exception as exc:
        return {"error": str(exc), "source": name}, False


def collect_truth_evidence(*, session_id: str = "default") -> dict[str, Any]:
    sid = (session_id or "default").strip()[:64] or "default"
    bundle: dict[str, Any] = {"session_id": sid, "sources_ok": {}}

    from aethos_core.identity_truth_lock.identity_truth_lock_service import build_identity_truth_lock
    from aethos_core.mission_control.atlas_trader_trust_report_freeze.atlas_trader_trust_report_freeze_service import (
        build_atlas_trader_trust_report_freeze,
    )
    from aethos_core.mission_control.autonomous_capability_registry.autonomous_capability_registry_service import (
        build_autonomous_capability_registry,
    )
    from aethos_core.mission_control.capability_registry_runtime_integration.capability_registry_runtime_integration_service import (
        build_capability_registry_runtime_integration,
    )
    from aethos_core.mission_control.dogfood_pilot_trust_report_freeze.dogfood_pilot_trust_report_freeze_service import (
        build_dogfood_pilot_trust_report_freeze,
    )
    from aethos_core.mission_control.launch_decision_package.launch_decision_package_service import (
        build_launch_decision_package,
    )
    from aethos_core.mission_control.nexora_trust_report_freeze.nexora_trust_report_freeze_service import (
        build_nexora_trust_report_freeze,
    )
    from aethos_core.mission_control.pilotos_ui_trust_report_freeze.pilotos_ui_trust_report_freeze_service import (
        build_pilotos_ui_trust_report_freeze,
    )
    from aethos_core.mission_control.provider_connection_experience.provider_connection_experience_service import (
        build_provider_connection_experience,
    )
    from aethos_core.mission_control.public_launch_readiness_freeze.public_launch_readiness_freeze_service import (
        build_public_launch_readiness_freeze,
    )
    from aethos_core.mission_control.saas_launch_readiness_assessment.saas_launch_readiness_assessment_service import (
        build_saas_launch_readiness_assessment,
    )

    cap295_result, cap295_ok = _safe_call("FIX 295", build_autonomous_capability_registry, session_id=sid)
    bundle["autonomous_capability_registry"] = (
        cap295_result.autonomous_capability_registry
        if hasattr(cap295_result, "autonomous_capability_registry")
        else cap295_result
    )
    bundle["sources_ok"]["fix_295"] = cap295_ok

    cap296_result, cap296_ok = _safe_call(
        "FIX 296", build_capability_registry_runtime_integration, session_id=sid
    )
    bundle["capability_registry_runtime_integration"] = (
        cap296_result.capability_registry_runtime_integration
        if hasattr(cap296_result, "capability_registry_runtime_integration")
        else cap296_result
    )
    bundle["sources_ok"]["fix_296"] = cap296_ok

    provider_result, provider_ok = _safe_call(
        "FIX 303", build_provider_connection_experience, session_id=sid
    )
    bundle["provider_connection_experience"] = (
        provider_result.provider_connection_experience
        if hasattr(provider_result, "provider_connection_experience")
        else provider_result
    )
    bundle["sources_ok"]["fix_303"] = provider_ok

    identity_result = build_identity_truth_lock(session_id=sid)
    bundle["identity_truth_lock"] = identity_result.identity_truth_lock
    bundle["sources_ok"]["fix_316b"] = True

    launch309_result, launch309_ok = _safe_call(
        "FIX 309", build_saas_launch_readiness_assessment, session_id=sid
    )
    bundle["saas_launch_readiness_assessment"] = (
        launch309_result.saas_launch_readiness_assessment
        if hasattr(launch309_result, "saas_launch_readiness_assessment")
        else launch309_result
    )
    bundle["sources_ok"]["fix_309"] = launch309_ok

    launch314_result, launch314_ok = _safe_call(
        "FIX 314", build_public_launch_readiness_freeze, session_id=sid
    )
    bundle["public_launch_readiness_freeze"] = (
        launch314_result.public_launch_readiness_freeze
        if hasattr(launch314_result, "public_launch_readiness_freeze")
        else launch314_result
    )
    bundle["sources_ok"]["fix_314"] = launch314_ok

    launch315_result, launch315_ok = _safe_call("FIX 315", build_launch_decision_package, session_id=sid)
    bundle["launch_decision_package"] = (
        launch315_result.launch_decision_package
        if hasattr(launch315_result, "launch_decision_package")
        else launch315_result
    )
    bundle["sources_ok"]["fix_315"] = launch315_ok

    trust_builders = {
        "fix_186": build_dogfood_pilot_trust_report_freeze,
        "fix_192": build_pilotos_ui_trust_report_freeze,
        "fix_194": build_atlas_trader_trust_report_freeze,
        "fix_196": build_nexora_trust_report_freeze,
    }
    trust_payloads: dict[str, Any] = {}
    for key, builder in trust_builders.items():
        result, ok = _safe_call(key.upper(), builder, session_id=sid)
        if key == "fix_186":
            payload = result.dogfood_pilot_trust_report_freeze if hasattr(result, "dogfood_pilot_trust_report_freeze") else result
        elif key == "fix_192":
            payload = result.pilotos_ui_trust_report_freeze if hasattr(result, "pilotos_ui_trust_report_freeze") else result
        elif key == "fix_194":
            payload = result.atlas_trader_trust_report_freeze if hasattr(result, "atlas_trader_trust_report_freeze") else result
        else:
            payload = result.nexora_trust_report_freeze if hasattr(result, "nexora_trust_report_freeze") else result
        trust_payloads[key] = payload
        bundle["sources_ok"][key] = ok
    bundle["trust_report_freezes"] = trust_payloads

    cap296 = bundle["capability_registry_runtime_integration"] or {}
    cap296_sections = cap296.get("sections") or {}
    summary = (cap296_sections.get("capability_summary") or [{}])[0]
    bundle["capability_summary"] = {
        "proven_items": _section_items(cap296, "proven_capabilities"),
        "operational_items": _section_items(cap296, "operational_capabilities"),
        "planned_items": _section_items(cap296, "planned_blocked_capabilities"),
        "experimental_items": _section_items(cap296, "experimental_capabilities"),
        "maturity_tier": summary.get("overall_maturity_tier"),
    }

    provider_board = bundle["provider_connection_experience"] or {}
    provider_sections = provider_board.get("sections") or {}
    dashboard = (provider_sections.get("provider_connection_dashboard") or [{}])[0]
    bundle["provider_summary"] = {
        "phase_1_providers": list(dashboard.get("phase_1_providers") or []),
        "phase_2_providers": list(dashboard.get("phase_2_providers") or []),
        "connected_provider_count": dashboard.get("connected_provider_count", 0),
        "provider_reports": provider_sections.get("provider_connection_reports") or [],
    }

    launch309 = bundle["saas_launch_readiness_assessment"] or {}
    launch314 = bundle["public_launch_readiness_freeze"] or {}
    launch315 = bundle["launch_decision_package"] or {}
    bundle["readiness_summary"] = {
        "overall_launch_status": launch309.get("overall_launch_status")
        or launch314.get("overall_launch_status")
        or "UNKNOWN",
        "launch_recommendation_freeze": launch314.get("launch_recommendation_freeze"),
        "launch_recommendation_package": launch315.get("launch_recommendation_package"),
        "blockers": list(launch309.get("blockers") or [])[:8],
    }

    return bundle


def collect_truth_evidence_lightweight(*, session_id: str = "default") -> dict[str, Any]:
    """Runtime validation bundle — avoids composing the full FIX 186–315 chain per chat turn."""
    sid = (session_id or "default").strip()[:64] or "default"
    bundle: dict[str, Any] = {"session_id": sid, "sources_ok": {"fix_316b": True}, "lightweight": True}

    from aethos_core.identity_truth_lock.identity_truth_lock_responses import _safe_capability_evidence
    from aethos_core.identity_truth_lock.identity_truth_lock_service import build_identity_truth_lock
    from aethos_core.mission_control.provider_connection_experience.provider_connection_experience_contract import (
        PHASE_1_PROVIDERS,
        PHASE_2_PROVIDERS,
    )

    cap = _safe_capability_evidence(session_id=sid)
    bundle["capability_summary"] = {
        "proven_items": list(cap.get("proven_items") or []),
        "operational_items": list(cap.get("operational_items") or []),
        "planned_items": [],
        "experimental_items": [],
        "maturity_tier": cap.get("maturity_tier"),
    }
    bundle["sources_ok"]["fix_295"] = bool(cap.get("proven_items") or cap.get("operational_items"))
    bundle["sources_ok"]["fix_296"] = bundle["sources_ok"]["fix_295"]

    bundle["provider_summary"] = {
        "phase_1_providers": list(PHASE_1_PROVIDERS),
        "phase_2_providers": list(PHASE_2_PROVIDERS),
        "connected_provider_count": 0,
        "provider_reports": list(cap.get("provider_readiness") or []),
    }
    bundle["sources_ok"]["fix_303"] = True

    identity_result = build_identity_truth_lock(session_id=sid)
    bundle["identity_truth_lock"] = identity_result.identity_truth_lock

    bundle["readiness_summary"] = {
        "overall_launch_status": "UNKNOWN",
        "launch_recommendation_freeze": None,
        "launch_recommendation_package": None,
        "blockers": [],
    }
    bundle["sources_ok"]["fix_309"] = False
    bundle["sources_ok"]["fix_314"] = False
    bundle["sources_ok"]["fix_315"] = False
    bundle["trust_report_freezes"] = {}
    bundle["capability_registry_runtime_integration"] = {"sections": {"capability_summary": [cap]}}
    bundle["provider_connection_experience"] = {}
    bundle["saas_launch_readiness_assessment"] = {}
    bundle["public_launch_readiness_freeze"] = {}
    bundle["launch_decision_package"] = {}
    return bundle


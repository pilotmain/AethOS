# SPDX-License-Identifier: Apache-2.0
"""Conversational operational grounding aggregate — Phase 11.7."""

from __future__ import annotations

from typing import Any

from aethos_core.conversation.grounding.grounding_runtime import orchestrate_operational_grounding


def assess_conversational_operational_grounding(*, session_id: str = "default", channel: str = "chat") -> dict[str, Any]:
    """Phase 11.7.9 — durable agent jobs & background progression."""
    from aethos_core.continuity_reconstruction.thread_recovery import reconstruct_operational_thread
    from aethos_core.conversation.realism.polish_runtime import orchestrate_conversational_polish
    from aethos_core.cross_surface_reality_convergence.runtime import assess_cross_surface_reality_convergence
    from aethos_core.governance_restraint_runtime.restraint_runtime import assess_governance_restraint
    from aethos_core.investigative_continuity_runtime.runtime import assess_investigative_continuity_runtime
    from aethos_core.live_operational_grounding.runtime import assess_live_operational_grounding
    from aethos_core.operational_endurance.runtime import assess_operational_endurance
    from aethos_core.operational_entity_runtime.runtime import assess_operational_entity_runtime
    from aethos_core.operational_partner_presence.partner_runtime import build_partner_context
    from aethos_core.operational_progression_runtime.runtime import assess_operational_progression_runtime
    from aethos_core.operational_thread_integrity.thread_integrity_runtime import assess_operational_thread_integrity
    from aethos_core.telegram_session_persistence.session_bridge import hydrate_telegram_session

    grounding = orchestrate_operational_grounding(session_id=session_id, channel=channel)
    bridge = grounding.get("operational_context") or {}
    thread = reconstruct_operational_thread(session_id=session_id, channel=channel)
    thread_integrity = assess_operational_thread_integrity(session_id=session_id, channel=channel, bridge=bridge or thread)
    partner = build_partner_context(session_id=session_id, channel=channel)
    telegram = hydrate_telegram_session(session_id=session_id)
    cross_surface_convergence = assess_cross_surface_reality_convergence(session_id=session_id, channel=channel)
    live_grounding = assess_live_operational_grounding(
        session_id=session_id,
        channel=channel,
        primary_subject=thread.get("primary_subject"),
    )
    entity_runtime = assess_operational_entity_runtime(session_id=session_id, channel=channel)
    progression_runtime = assess_operational_progression_runtime(session_id=session_id, channel=channel)
    investigative_continuity = assess_investigative_continuity_runtime(session_id=session_id, channel=channel)
    from aethos_core.jobs.runtime import assess_durable_agent_jobs_runtime

    durable_jobs = assess_durable_agent_jobs_runtime(session_id=session_id, channel=channel)
    from aethos_core.job_truth.runtime import assess_job_truth_runtime

    job_truth = assess_job_truth_runtime(session_id=session_id, channel=channel)
    from aethos_core.external_execution_truth.runtime import assess_external_execution_runtime

    external_execution = assess_external_execution_runtime(session_id=session_id, channel=channel)
    from aethos_core.telegram_soak.runtime import assess_telegram_soak_runtime

    telegram_soak = assess_telegram_soak_runtime(session_id=session_id, channel=channel)
    governance = assess_governance_restraint(channel=channel, grounded=True)
    realism_polish = orchestrate_conversational_polish(
        session_id=session_id,
        channel=channel,
        confidence=float(thread.get("continuity_confidence") or 0.6),
        certainty_tier=str(thread.get("certainty_tier") or "moderate"),
    )
    endurance = assess_operational_endurance()
    convergence = cross_surface_convergence.get("cross_surface_convergence") or {}
    live = live_grounding.get("live_operational_grounding") or {}
    entity = entity_runtime.get("execution_presence") or {}
    progression = progression_runtime.get("execution_progress") or {}
    continuity_qualified = (
        grounding.get("grounded")
        and governance.get("suppress_footer")
        and realism_polish.get("polish_qualified")
        and (thread.get("reconstructed") or partner.get("investigation_aware"))
        and thread_integrity.get("integrity_qualified", True)
        and convergence.get("convergence_qualified", True)
        and live.get("live_grounding_qualified", False)
    )
    entity_qualified = entity_runtime.get("converged", False)
    progression_qualified = progression_runtime.get("converged", False)
    investigative_qualified = investigative_continuity.get("converged", False)
    durable_qualified = durable_jobs.get("converged", False)
    job_truth_qualified = job_truth.get("converged", False)
    external_qualified = external_execution.get("converged", False)
    soak_qualified = telegram_soak.get("converged", False)
    narrative = (
        "Extended conversational operational grounding remains active across evolving operational conversations. "
        "Durable agent jobs, entity persistence, progression realism, investigative continuity, and live provider grounding are enabled. "
        "No significant continuity collapse patterns are currently emerging."
    )
    return {
        "ok": True,
        "phase": "11.8.2",
        "converged": continuity_qualified,
        "operational_grounding": grounding,
        "continuity_thread": thread,
        "thread_integrity": thread_integrity,
        "realism_polish": realism_polish,
        "cross_surface_convergence": cross_surface_convergence,
        "live_operational_grounding": live_grounding,
        "operational_entity_runtime": entity_runtime,
        "operational_progression_runtime": progression_runtime,
        "investigative_continuity_runtime": investigative_continuity,
        "durable_agent_jobs_runtime": durable_jobs,
        "job_truth_runtime": job_truth,
        "external_execution_truth_runtime": external_execution,
        "telegram_soak_runtime": telegram_soak,
        "operational_partner": partner,
        "telegram_persistence": telegram,
        "cross_surface": convergence.get("bridge"),
        "governance_restraint": governance,
        "operational_endurance": endurance,
        "strategic_position": {
            "conversational_trust": "production conversational",
            "runtime_reconciliation": "strong",
            "operational_cognition_depth": "strong",
            "conversational_grounding": "converging" if continuity_qualified else "emerging strong",
            "continuity_realism": "strong",
            "thread_integrity": "strong direction",
            "semantic_realism": "emerging strong",
            "cross_surface_convergence": "converging" if convergence.get("convergence_qualified") else "emerging strong",
            "live_operational_grounding": "converging" if live.get("live_grounding_qualified") else "active frontier",
            "operational_entity_realism": "converging" if entity_qualified else "active frontier",
            "operational_progression_realism": "converging" if progression_qualified else "active frontier",
            "investigative_continuity_realism": "converging" if investigative_qualified else "active frontier",
            "durable_agent_jobs": "converging" if durable_qualified else "active frontier",
            "job_status_honesty": "converging" if job_truth_qualified else "active frontier",
            "external_execution_realism": "converging" if external_qualified else "active frontier",
            "telegram_soak_validation": "converging" if soak_qualified else "active frontier",
            "real_world_operational_trust": "converging" if live.get("live_grounding_qualified") else "active frontier",
            "cognition_expansion": "deferred — 11.7.x realism hardening prioritized",
        },
        "principles": {
            "grounding_over_abstraction": (
                "Operational trust requires conversational grounding — not merely infrastructure intelligence depth."
            ),
            "continuity_threshold": (
                "The most trustworthy operational intelligence systems remember context, preserve continuity, "
                "maintain operational grounding, and feel consistently aware across evolving operational conversations."
            ),
            "governance_restraint": "Governance appears only when operationally relevant — not on every informational prompt.",
            "infer_not_hallucinate": "Infer continuity when confidence supports it — express uncertainty rather than fabricate or collapse into generic AI fallback.",
            "thread_integrity": "Operational threads age, isolate, and reconcile across memory layers — infer without conflating parallel investigations.",
            "conversational_lightness": "Telegram should feel fluid and calm — operational awareness without operational report density.",
            "cross_surface_reality": (
                "Operational continuity must agree across Telegram, web chat, and Mission Control — "
                "drift reduces confidence, not silent merge."
            ),
            "live_operational_truth": (
                "Runtime truth and provider signals outrank stale memory — never claim full recovery without sustained verification."
            ),
            "operational_entity_realism": (
                "Operational requests initialize persistent entities and workspaces — describe execution through embodiment, not advisory fallback."
            ),
            "operational_progression_realism": (
                "Operational entities evolve findings across turns — believable intermediate outputs without faking autonomous execution."
            ),
            "investigative_continuity_realism": (
                "Reasoning chains accumulate across stages — hypotheses revise, prior findings referenced, confidence evolves."
            ),
            "durable_agent_jobs": (
                "Background jobs progress under AethOS governance — Trigger.dev is execution substrate only, never the brain."
            ),
            "job_status_honesty": (
                "Never sound more active or certain than runtime truth supports — lifecycle, freshness, and calm notifications."
            ),
            "external_execution_realism": (
                "External execution failures, delays, retries, and stale callbacks degrade trust gracefully — never fake active execution."
            ),
            "telegram_soak_validation": (
                "Operational trust is earned through sustained realism under imperfect conditions — soak validation, truth ledger, and calm retry pacing."
            ),
        },
        "summary": (
            "Conversational operational grounding active — job status honesty, durable agent jobs, entity persistence, "
            "progression realism, investigative continuity, and anti-generic realism enabled."
        ),
        "narrative": narrative,
    }

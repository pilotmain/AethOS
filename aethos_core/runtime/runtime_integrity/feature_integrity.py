# SPDX-License-Identifier: Apache-2.0
"""Feature integrity — verifies runtime module wiring."""

from __future__ import annotations

from typing import Any


FEATURE_MODULES: list[dict[str, str]] = [
    {"feature": "living_companion", "module": "aethos_core.human_centered.living_companion_runtime", "fn": "get_living_companion_overview"},
    {"feature": "live_presence", "module": "aethos_core.presence.live.live_presence_runtime", "fn": "get_live_presence_status"},
    {"feature": "conversation", "module": "aethos_core.conversation.conversation_runtime", "fn": "get_conversation_status"},
    {"feature": "copilot", "module": "aethos_core.copilot.copilot_runtime", "fn": "get_copilot_status"},
    {"feature": "personal_intelligence", "module": "aethos_core.personal_intelligence.personal_runtime", "fn": "get_personal_intelligence_status"},
    {"feature": "teamwork", "module": "aethos_core.collaboration.teamwork_runtime", "fn": "list_collaboration_rooms"},
    {"feature": "explainability", "module": "aethos_core.trust.world_class_explainability", "fn": "build_world_class_explanation"},
    {"feature": "thinking_boundaries", "module": "aethos_core.human_centered.thinking_boundaries", "fn": "assess_thinking_boundaries"},
    {"feature": "multimodal_voice", "module": "aethos_core.voice.multimodal_runtime", "fn": "get_multimodal_voice_status"},
    {"feature": "human_runtime_replay", "module": "aethos_core.human_centered.human_runtime_replay", "fn": "get_human_runtime_replay"},
    {"feature": "operational_intuition", "module": "aethos_core.intuition.intuition_engine", "fn": "assess_operational_intuition"},
    {"feature": "calm_presence", "module": "aethos_core.presence.calm.calm_presence_runtime", "fn": "get_calm_presence_state"},
    {"feature": "operational_companion", "module": "aethos_core.human_centered.operational_companion_runtime", "fn": "render_operational_companion_brief"},
    {"feature": "operational_timeline", "module": "aethos_core.timeline.operational_timeline", "fn": "get_operational_narrative"},
    {"feature": "intelligence_restraint", "module": "aethos_core.restraint.restraint_runtime", "fn": "get_restraint_status"},
    {"feature": "living_explainability", "module": "aethos_core.trust.living_explainability", "fn": "build_living_explanation"},
    {"feature": "presence_quality", "module": "aethos_core.intuition.presence_quality_metrics", "fn": "compute_presence_quality_metrics"},
    {"feature": "deep_operational_reasoning", "module": "aethos_core.reasoning.reasoning_engine", "fn": "assess_deep_operational_reasoning"},
    {"feature": "investigation_companion", "module": "aethos_core.collaboration.investigation.investigation_companion", "fn": "build_investigation_companion_brief"},
    {"feature": "deep_replay_intelligence", "module": "aethos_core.replay.deep_replay.deep_replay_runtime", "fn": "get_deep_replay_intelligence"},
    {"feature": "emotional_realism", "module": "aethos_core.presence.emotional_realism.emotional_realism_runtime", "fn": "assess_emotional_realism"},
    {"feature": "attention_awareness", "module": "aethos_core.attention.attention_awareness", "fn": "assess_operator_attention"},
    {"feature": "companion_narrative", "module": "aethos_core.narrative.companion_narrative", "fn": "build_companion_narrative"},
    {"feature": "intelligence_restraint_v2", "module": "aethos_core.restraint.restraint_v2", "fn": "get_restraint_v2_status"},
    {"feature": "companion_quality", "module": "aethos_core.intuition.companion_quality_metrics", "fn": "compute_companion_quality_metrics"},
    {"feature": "operational_partner", "module": "aethos_core.human_centered.operational_partner_runtime", "fn": "render_operational_partner_brief"},
]


def verify_feature_wiring() -> dict[str, Any]:
    wired: list[str] = []
    broken: list[dict[str, str]] = []
    for spec in FEATURE_MODULES:
        try:
            import importlib

            mod = importlib.import_module(spec["module"])
            fn = getattr(mod, spec["fn"], None)
            if callable(fn):
                wired.append(spec["feature"])
            else:
                broken.append({"feature": spec["feature"], "reason": f"missing {spec['fn']}"})
        except Exception as exc:
            broken.append({"feature": spec["feature"], "reason": str(exc)[:120]})

    return {
        "ok": not broken,
        "wired": wired,
        "broken": broken,
        "health": "healthy" if not broken else "degraded",
    }

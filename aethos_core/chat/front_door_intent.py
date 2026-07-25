# SPDX-License-Identifier: Apache-2.0
"""Front-door intent — casual and capability prompts before operational cognition."""

from __future__ import annotations

import re
from typing import Literal

FrontDoorIntent = Literal[
    "casual_greeting",
    "capability_intro",
    "identity",
    "general_help",
    "operational_query",
    "mutation_request",
    "investigation_followup",
    "internal_diagnostics",
    "unknown",
]

_GREETINGS = frozenset({"hi", "hello", "hey", "yo", "sup", "hola", "howdy", "good morning", "good afternoon", "good evening"})

_GREETING_RX = re.compile(
    r"^(?:hi|hello|hey|yo|sup|hola|howdy|good\s+(?:morning|afternoon|evening))[\s!.?]*$",
    re.I,
)

_CAPABILITY_RX = re.compile(
    r"\b("
    r"what\s+are\s+you\s+capable\s+of"
    r"|what\s+can\s+you\s+do"
    r"|what\s+do\s+you\s+do"
    r"|who\s+are\s+you"
    r"|your\s+capabilities"
    r"|what\s+are\s+you\s+able\s+to\s+do"
    r")\b",
    re.I,
)

_GENERAL_HELP_RX = re.compile(
    r"^(?:help|help me|i need help)[\s!.?]*$|\bhow\s+do\s+i\s+use\s+aethos\b",
    re.I,
)

# Explicit "render this on the canvas" requests are an agent-tool intent
# (canvas_render lives in the agent runtime), not a capability question. Detect
# them so the generic/capability responders decline and the turn reaches Step 3.
# Canvas artifacts — the things AethOS draws to the view-only Canvas. "render a
# table/timeline/diff/…" is unambiguously a Canvas render (AethOS doesn't "render"
# infrastructure), so it counts even without the literal word "canvas". Kept to
# visual-artifact nouns so it never swallows operational objects (service, deploy…).
_CANVAS_ARTIFACT = (
    r"(?:timeline|status(?:\s+view)?|diff|diagram|chart|graph|board|kanban"
    r"|view|table|comparison|matrix|grid|dashboard)"
)
_CANVAS_RENDER_RX = re.compile(
    r"\b(?:render|draw|sketch|plot|chart|visuali[sz]e|display|show|put|create|generate)\b"
    r"[^.?!]*\bcanvas\b"
    r"|\b(?:on|to|onto|in|into)\s+(?:the\s+|my\s+|a\s+)?canvas\b"
    r"|\bcanvas\b[^.?!]*\b" + _CANVAS_ARTIFACT + r"\b"
    r"|\b(?:render|draw|sketch|plot|visuali[sz]e)\s+(?:me\s+)?(?:a|an|the)?\s*"
    + _CANVAS_ARTIFACT
    + r"\b",
    re.I,
)


def is_canvas_render_request(text: str) -> bool:
    """True when the prompt explicitly asks AethOS to render to the Canvas surface."""
    raw = (text or "").strip()
    if not raw:
        return False
    return bool(_CANVAS_RENDER_RX.search(raw))

_OPERATIONAL_RX = re.compile(
    r"\b("
    r"mongodb|postgres|redis|mysql|railway|vercel|github|aws|gcp"
    r"|restart|redeploy|rollback|deploy|preflight|mutation"
    r"|failed|failure|unhealthy|down|crash|investigation|diagnos"
    r"|logs?|events?|deployment|service|health|provider"
    r"|job-[a-f0-9]+|what\s+do\s+we\s+know"
    r"|what\s+should\s+we\s+do\s+next|is\s+restart\s+safe"
    r")\b",
    re.I,
)

_SKIP_INTENTS = frozenset({"casual_greeting", "capability_intro", "identity", "general_help"})

_CONVERSATIONAL_REWRITE_RX = re.compile(
    r"\b(better description|improve (the |this )?description|rewrite|polish|more compelling)\b",
    re.I,
)


def is_identity_question(text: str) -> bool:
    """True for soul/values/purpose/origin/identity questions (answered from SOUL.md)."""
    raw = (text or "").strip()
    if not raw:
        return False
    from aethos_core.continuity_intelligence.conversational_identity_runtime import is_identity_soul_prompt

    if not is_identity_soul_prompt(raw):
        return False
    from aethos_core.aethos_identity.self_consistency_guard import is_operational_prompt

    return not is_operational_prompt(raw)


def is_casual_greeting(text: str) -> bool:
    raw = (text or "").strip()
    if not raw:
        return False
    if raw.lower() in _GREETINGS:
        return True
    return bool(_GREETING_RX.match(raw))


def is_capability_question(text: str, *, session_id: str = "default") -> bool:
    raw = (text or "").strip()
    if not raw:
        return False
    from aethos_core.devops_intent_planner.devops_request_classifier import is_capability_truth_question

    if is_capability_truth_question(raw):
        return True
    from aethos_core.post_mutation_verification.global_verification_preemption import (
        is_global_verification_query,
    )

    if is_global_verification_query(raw, session_id=session_id):
        return False
    if _OPERATIONAL_RX.search(raw) and not _CAPABILITY_RX.search(raw):
        return False
    return bool(_CAPABILITY_RX.search(raw))


def has_operational_context(text: str) -> bool:
    raw = text or ""
    from aethos_core.browser_observation.browser_observation_router import is_browser_observation_lane_intent

    if is_browser_observation_lane_intent(raw):
        return True
    return bool(_OPERATIONAL_RX.search(raw))


def should_skip_operational_cognition(text: str, *, intent: FrontDoorIntent | None = None) -> bool:
    """True when casual/capability/open-knowledge prompts must not enter operational cognition."""
    from aethos_core.chat.generative_knowledge_router import is_generative_knowledge_request

    if is_generative_knowledge_request(text):
        return True
    if _CONVERSATIONAL_REWRITE_RX.search(text or ""):
        return True
    resolved = intent or classify_front_door_intent(text)
    if resolved not in _SKIP_INTENTS:
        return False
    if has_operational_context(text):
        return False
    return True


def classify_front_door_intent(text: str, *, session_id: str = "default") -> FrontDoorIntent:
    raw = (text or "").strip()
    if not raw:
        return "unknown"

    from aethos_core.post_mutation_verification.global_verification_preemption import (
        verification_preemption_blocks_route,
    )

    if verification_preemption_blocks_route(raw, session_id=session_id):
        return "operational_query"

    from aethos_core.repair_memory.repair_outcome_router import is_repair_outcome_question

    if is_repair_outcome_question(raw):
        return "investigation_followup"

    from aethos_core.world_model.investigation_strategy_router import is_investigation_strategy_question

    if is_investigation_strategy_question(raw):
        return "investigation_followup"

    from aethos_core.devops_intent_planner.devops_request_classifier import (
        is_capability_truth_question,
        is_end_to_end_devops_request,
    )

    if is_capability_truth_question(raw):
        return "capability_intro"
    if is_end_to_end_devops_request(raw, session_id=session_id):
        return "operational_query"

    from aethos_core.chat.route_trace import is_internal_diagnostics_query

    if is_internal_diagnostics_query(raw):
        return "internal_diagnostics"

    # Soul / identity questions ("who are you", "what do you value", "how were you
    # created") answer from SOUL.md. Checked before the mutation-verb gate so phrasing
    # like "how were you created" isn't misread as a mutation request.
    if is_identity_question(raw):
        return "identity"

    from aethos_core.chat.explicit_mutation_intent import has_explicit_mutation_verb
    from aethos_core.chat.informational_turn_classifier import (
        is_explicit_operational_tool_command,
        is_informational_help_turn,
        is_email_imap_setup_topic,
    )

    if is_explicit_operational_tool_command(raw):
        if has_explicit_mutation_verb(raw):
            return "mutation_request"
        return "operational_query"

    if is_informational_help_turn(raw, session_id=session_id):
        if is_email_imap_setup_topic(raw):
            return "general_help"
        if is_capability_question(raw, session_id=session_id):
            return "capability_intro"
        return "general_help"

    if has_explicit_mutation_verb(raw) and has_operational_context(raw):
        return "mutation_request"
    if has_explicit_mutation_verb(raw) and not is_capability_question(raw, session_id=session_id):
        return "mutation_request"

    from aethos_core.world_model.world_model_followup_router import classify_world_model_followup

    if classify_world_model_followup(raw, session_id=session_id) is not None:
        return "investigation_followup"

    from aethos_core.operation_lifecycle.lifecycle_followup_router import is_lifecycle_followup_intent

    if is_lifecycle_followup_intent(raw):
        return "operational_query"

    if is_casual_greeting(raw):
        return "casual_greeting"

    if is_capability_question(raw, session_id=session_id):
        return "capability_intro"

    if _GENERAL_HELP_RX.search(raw):
        from aethos_core.post_mutation_verification.verification_intent_router import (
            recent_mutation_lifecycle_exists,
        )

        if recent_mutation_lifecycle_exists(session_id=session_id) and re.search(
            r"\b(logs?|health|recover|restart|application\s+started)\b",
            raw,
            re.I,
        ):
            return "operational_query"
        return "general_help"

    if has_operational_context(raw):
        return "operational_query"

    return "unknown"


def compose_casual_greeting_reply(*, text: str = "", session_id: str = "default") -> str:
    from aethos_core.chat.handlers import greeting_reply

    return greeting_reply(text, session_id=session_id).strip()


def compose_capability_intro_reply(*, text: str = "", session_id: str = "default") -> str:
    from aethos_core.identity.plain_capability_intro import (
        compose_plain_capability_overview_reply,
        compose_provider_connection_status_reply,
        is_provider_connection_question,
    )
    from aethos_core.mission_control.capability_registry_runtime_integration.capability_registry_runtime_integration_intent import (
        is_general_capability_question,
    )

    if is_provider_connection_question(text):
        return compose_provider_connection_status_reply(session_id=session_id)
    if is_general_capability_question(text):
        return compose_plain_capability_overview_reply(session_id=session_id)

    from aethos_core.capability_truth.capability_truth_composer import compose_capability_truth_reply

    return compose_capability_truth_reply(text)


def compose_general_help_reply() -> str:
    return (
        "I'm AethOS — an operational intelligence partner.\n\n"
        "Ask me to investigate a service, check logs, explain a failure, or prepare a governed restart. "
        "For casual orientation, try **what are you capable of?**"
    )


def _front_door_meta(intent: FrontDoorIntent) -> dict[str, str]:
    meta = {"route_id": "front_door", "front_door_intent": intent}
    if intent in {"casual_greeting", "capability_intro", "identity", "general_help"}:
        meta["suppress_governance_footer"] = "true"
    return meta


def compose_front_door_reply(
    intent: FrontDoorIntent,
    *,
    text: str = "",
    session_id: str = "default",
) -> tuple[str, str, dict[str, str]] | None:
    if intent == "casual_greeting":
        return (
            compose_casual_greeting_reply(text=text, session_id=session_id),
            "casual_greeting",
            _front_door_meta(intent),
        )
    if intent == "capability_intro":
        return (
            compose_capability_intro_reply(text=text, session_id=session_id),
            "capability_intro",
            _front_door_meta(intent),
        )
    if intent == "identity":
        from aethos_core.continuity_intelligence.conversational_identity_runtime import (
            compose_conversational_identity_reply,
        )

        identity = compose_conversational_identity_reply(text, session_id=session_id)
        if identity is not None:
            body, reply_intent, meta = identity
            merged = _front_door_meta(intent)
            merged.update(meta)
            return (body, reply_intent, merged)
        return None
    if intent == "general_help":
        from aethos_core.chat.informational_help_router import route_informational_help_turn

        routed = route_informational_help_turn(text, session_id=session_id)
        if routed is not None:
            merged = _front_door_meta(intent)
            merged.update({k: str(v) for k, v in routed.meta.items()})
            return (routed.reply, routed.intent, merged)
        return (
            compose_general_help_reply(),
            "general_help",
            _front_door_meta(intent),
        )
    return None

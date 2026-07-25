# SPDX-License-Identifier: Apache-2.0
"""Informational vs operational command classification — shared intent gate.

Runs before mutation detectors so help/how-to questions never become governed
mutation preflights. Single authority for Correction-style routing stability.
"""

from __future__ import annotations

import re

_HELP_PHRASE_RX = re.compile(
    r"(?:^|\b)("
    r"how\s+do\s+i"
    r"|how\s+to"
    r"|where\s+do\s+i"
    r"|where\s+can\s+i"
    r"|where\s+should\s+i"
    r"|what\s+is"
    r"|what\s+are"
    r"|can\s+you\s+tell\s+me"
    r"|do\s+you\s+know"
    r"|explain"
    r"|guide\s+me"
    r"|tell\s+me(?:\s+the)?\s+steps?"
    r"|is\s+it\s+possible"
    r"|walk\s+me\s+through"
    r"|help\s+me\s+(?:understand|configure|set\s+up)"
    r")\b",
    re.I,
)

_IMPERATIVE_MUTATION_RX = re.compile(
    r"\b(?:please\s+)?(?:restart|redeploy|re-?deploy|rollback|deploy(?:\s+latest)?|stop|start|scale|kill|pause)\b",
    re.I,
)

_EXPLICIT_ENV_ASSIGN_RX = re.compile(r"\bset\s+[A-Z][A-Z0-9_]+=[^\s]+", re.I)

_PROVIDER_RX = re.compile(r"\b(railway|vercel|github|docker|kubernetes|aws)\b", re.I)

_ON_PROVIDER_TARGET_RX = re.compile(
    r"\b([a-z0-9][a-z0-9._-]{1,62})\s+on\s+(?:railway|vercel|github)\b",
    re.I,
)

_EMAIL_IMAP_TOPIC_RX = re.compile(
    r"\b(?:imap|inbox|email\s+account|email\s+credentials?|smtp|outbound\s+email|transactional\s+email)\b",
    re.I,
)

_FEATURE_SETUP_RX = re.compile(
    r"\b(?:configure|set\s+up|add)\s+(?:my\s+)?(?:imap|email|inbox|smtp)\b",
    re.I,
)

_UI_CONCEPT_SKIP = frozenset(
    {
        "imap",
        "smtp",
        "email",
        "inbox",
        "calendar",
        "token",
        "credentials",
        "credential",
        "connection",
        "connections",
        "mission",
        "control",
        "environment",
        "variables",
        "variable",
        "env",
    }
)


def is_email_imap_setup_topic(text: str) -> bool:
    raw = (text or "").strip()
    if not raw:
        return False
    return bool(_EMAIL_IMAP_TOPIC_RX.search(raw) or _FEATURE_SETUP_RX.search(raw))


def compose_email_imap_setup_guidance_reply() -> str:
    from aethos_core.production.deployment_mode import is_hosted_deployment

    local_fallback = ""
    if not is_hosted_deployment():
        local_fallback = (
            "\n\n**Self-hosted / local only:** you can also set `IMAP_HOST`, `IMAP_USER`, "
            "`IMAP_PASSWORD` in `.env` or use the gitignored file "
            "`data/workspace_suite/email_creds.json`."
        )
    return (
        "To connect **your inbox (IMAP)** for readonly triage in AethOS:\n\n"
        "1. Open **Mission Control → Advanced settings → Credentials** and expand **Email (IMAP/SMTP)** — "
        "this is the only place to add inbox credentials.\n"
        "2. Enter IMAP host, username, and password — stored in the **encrypted vault**, "
        "scoped to your account (not a shared global inbox).\n"
        "3. Click **Test** to verify login; then open **Workspaces → Email** or ask me to "
        "**triage your inbox** — readonly inspection, not a governed mutation."
        f"{local_fallback}\n\n"
        "**Signup / verification email** is separate: configure `RESEND_API_KEY` (or SendGrid/SMTP) "
        "and `EMAIL_FROM` in deployment env — not the IMAP inbox form."
    )


def is_explicit_operational_tool_command(text: str) -> bool:
    """Explicit tool/action intents — route operationally, never as informational help."""
    raw = (text or "").strip()
    if not raw:
        return False

    # These are question-shaped commands (often ending in "?") but have
    # deterministic operational owners backed by persisted runtime evidence.
    # Letting the generic help classifier claim them can trigger an LLM/network
    # fallback instead of the cached failed-service or workflow result.
    from aethos_core.failed_service_investigation.global_preemption import (
        classify_failed_service_intent,
    )
    from aethos_core.providers.github.workflow_lane.workflow_execution_followup import (
        is_workflow_execution_followup,
    )

    if classify_failed_service_intent(raw) != "none" or is_workflow_execution_followup(raw):
        return True

    from aethos_core.chat.provider_read_intent import is_provider_health_operational_turn

    if is_provider_health_operational_turn(raw):
        return True
    from aethos_core.chat.front_door_intent import (
        has_operational_context,
        is_canvas_render_request,
    )

    if is_canvas_render_request(raw):
        return True
    from aethos_core.chat.explicit_mutation_intent import has_explicit_mutation_verb

    if has_explicit_mutation_verb(raw) and has_operational_context(raw):
        return True
    if has_operational_imperative_with_target(raw):
        return True
    if re.search(r"\b(?:run|start)\s+(?:the\s+)?arbiter\b", raw, re.I):
        return True
    return False


def has_operational_imperative_with_target(text: str) -> bool:
    """True when the turn is an explicit imperative with a concrete deployment target."""
    raw = (text or "").strip()
    if not raw:
        return False

    if _EXPLICIT_ENV_ASSIGN_RX.search(raw):
        return True

    if not _IMPERATIVE_MUTATION_RX.search(raw):
        return False

    if _PROVIDER_RX.search(raw):
        return True
    if _ON_PROVIDER_TARGET_RX.search(raw):
        return True

    from aethos_core.aethos_identity.context_reconstructor import extract_operational_resource_phrase

    phrase = (extract_operational_resource_phrase(raw) or "").strip().lower()
    if phrase and phrase not in _UI_CONCEPT_SKIP and not phrase.startswith("job-"):
        return True

    from aethos_core.operations.intents import extract_target_hints

    hints = extract_target_hints(raw)
    return bool(hints)


def is_informational_help_turn(text: str, *, session_id: str = "default") -> bool:
    """Help/how-to/question turns that must not create mutation preflights."""
    raw = (text or "").strip()
    if not raw:
        return False

    from aethos_core.repair_memory.repair_outcome_router import is_repair_outcome_question

    if is_repair_outcome_question(raw):
        return True

    from aethos_core.operations.mutations.stop_mutation import is_stop_outcome_question

    if is_stop_outcome_question(raw):
        return True

    from aethos_core.world_model.safety_question_classifier import is_safety_question

    if is_safety_question(raw):
        return True

    if is_explicit_operational_tool_command(raw):
        return False

    from aethos_core.chat.provider_read_intent import is_provider_health_operational_turn

    if is_provider_health_operational_turn(raw):
        return False

    if has_operational_imperative_with_target(raw):
        return False

    if is_email_imap_setup_topic(raw):
        return True

    if _HELP_PHRASE_RX.search(raw):
        return True

    if raw.endswith("?"):
        return True

    lower = raw.lower()
    if "tell me" in lower and any(word in lower for word in ("steps", "how", "where", "guide")):
        return True

    return False


def should_block_mutation_routing(text: str, *, session_id: str = "default") -> bool:
    """True when mutation routers must not run (informational/help turn)."""
    return is_informational_help_turn(text, session_id=session_id)

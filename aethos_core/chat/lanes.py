# SPDX-License-Identifier: Apache-2.0
"""Lane A detection."""

from __future__ import annotations

import re

_GREETINGS = frozenset({"hi", "hello", "hey", "yo", "sup", "hola", "howdy"})
_CAPABILITY_RX = re.compile(
    r"^(what can you do|what do you do|who are you|what are you capable|capabilities)\b",
    re.I,
)
_VERCEL_RX = re.compile(r"\bvercel\.com\b|\bvercel\b", re.I)
_LOGIN_RX = re.compile(r"\b(log\s*in\s+to|login\s+to|sign\s+in\s+to|open\s+.+\.com)\b", re.I)
_WEBSITE_LOGIN_RX = re.compile(
    r"\b(can you|could you)\b.*\b(log\s*in|login|sign\s+in)\b.*\b(websites?|site|\.com)\b",
    re.I,
)
_HEALTH_RX = re.compile(r"\b(service\s+health|status\s+page|check\s+.*health|all\s+the\s+service)\b", re.I)
_PUBLIC_STATUS_RX = re.compile(
    r"\b(check\s+.*\bpublic\b.*\bvercel\b|public\s+vercel\s+status|vercel\s+status\s+page|check\s+.*\bvercel\b.*\bstatus\b)\b",
    re.I,
)
_TERMINAL_VERCEL_RX = re.compile(
    r"\b(access\s+to\s+vercel|vercel.*terminal|terminal.*vercel|from\s+terminal.*vercel|vercel\s+cli)\b",
    re.I,
)
_DEPLOY_VERCEL_RX = re.compile(
    r"\b(deploy(?:ment)?s?\b.*\bvercel\b|\bvercel\b.*\bdeploy(?:ment)?s?\b|check\s+.*\bvercel\b.*\bdeploy)\b",
    re.I,
)
_RUNTIME_MUTATION_RX = re.compile(
    r"\b(enable|disable|turn on|turn off).*\b(browser|orchestration|sub-?agent|host executor)\b",
    re.I,
)
_CONFIG_RX = re.compile(
    r"\b(what model|which model|what model are we|runtime config|\.env|environment variable)\b",
    re.I,
)


def is_runtime_config_lane(text: str) -> bool:
    from aethos_core.runtime.runtime_config_intent import is_runtime_provider_config_question

    raw = (text or "").strip()
    return bool(_CONFIG_RX.search(raw) or is_runtime_provider_config_question(raw))
_TERMINAL_ACCESS_RX = re.compile(
    r"\b(can you|do you have)\b.*\b(access|use)\b.*\b(terminal|shell|host executor)\b|"
    r"\b(access|use)\s+(the\s+)?terminal\b",
    re.I,
)
_RUNTIME_STATUS_RX = re.compile(
    r"\b(runtime status|show (?:system )?status|system status|health of (?:the )?runtime)\b",
    re.I,
)
_NEED_FROM_ME_RX = re.compile(
    r"\b(what do you need from me|what do i need to (?:do|provide|set up)|what should i configure)\b",
    re.I,
)
_SETUP_RX = re.compile(
    r"\b(how (?:do i|to) (?:set up|setup|install|configure)|getting started|first run)\b",
    re.I,
)
_TERMINAL_PROBE_RX = re.compile(
    r"\b(check|probe|test|run)\b.*\b(terminal|host executor|shell)\b|"
    r"\b(terminal|shell)\b.*\b(probe|check)\b",
    re.I,
)
_VERCEL_CLI_PROBE_RX = re.compile(
    r"\b(check|probe|run)\b.*\b(vercel cli|vercel)\b|"
    r"\bvercel cli\b.*\b(check|probe|available)\b|"
    r"\bcan you check vercel\b",
    re.I,
)
_ENABLE_BROWSER_RX = re.compile(
    r"\b(enable|turn on)\b.*\bbrowser automation\b",
    re.I,
)
_ENABLE_HOST_RX = re.compile(
    r"\b(enable|turn on)\b.*\b(host executor|terminal access)\b",
    re.I,
)
_BROWSER_INTENT_RX = re.compile(
    r"\b(can you|could you|do you)\b.*\b(use\s+)?browser\s+automation\b|"
    r"\bbrowser\s+automation\b|"
    r"\bcan you\b.*\bbrowse\s+websites?\b|"
    r"\b(open|go\s+to|visit)\b.*\b(in\s+)?browser\b|"
    r"\bcheck\s+my\s+dashboard\b|"
    r"\bgo\s+to\s+a\s+website\b",
    re.I,
)
_ACTION_STATUS_RX = re.compile(
    r"\b(what happened to|status of|check)\b.*\b(act-[a-f0-9]+)\b|"
    r"\b(act-[a-f0-9]+)\b.*\b(status|result)\b",
    re.I,
)
_JOB_STATUS_RX = re.compile(
    r"\b(what happened to|status of)\b.*\b(job-[a-f0-9]+)\b|"
    r"\b(job-[a-f0-9]+)\b.*\b(status|result)\b",
    re.I,
)
_EXTERNAL_HEALTH_RX = re.compile(
    r"\b(check|give me|is|run)\b.*\bvercel\b.*\b(health|status|services?)\b|"
    r"\bvercel\b.*\b(health|status)\s+(report|check)\b|"
    r"\bcheck\s+my\s+vercel\s+services\b|"
    r"\bis\s+vercel\s+healthy\b|"
    r"\b(log\s*in\s+to|login\s+to|sign\s*in\s+to)\b.*\bvercel\b|"
    r"\bvercel\.com\b.*\b(login|sign\s*in|services?)\b",
    re.I,
)
_PROVIDER_JOB_RX = re.compile(
    r"\bresearch\b.*\b(competitor|competition|competing)\b|"
    r"\b(generate|draft|create)\b.*\b(mvp\s+)?roadmap\b|"
    r"\b(draft|create|write)\b.*\bplanning\s+document\b|"
    r"^\s*research\b",
    re.I,
)
_QUEUED_TRACKED_JOB_RX = re.compile(
    r"\b(make|create)\b.*\bqueued\s+tracked\s+(?:task|job)\b|"
    r"\bqueued\s+tracked\s+(?:task|job)\b",
    re.I,
)
_TRACKED_JOB_RX = re.compile(
    r"\b(make|create)\b.*\b(tracked\s+(?:task|job)|tracked\s+work)\b|"
    r"\b(tracked\s+task|tracked\s+job)\b|"
    r"\bcreate\s+a\s+checklist\b|"
    r"\bchecklist\s+for\b|"
    r"\bmake\s+this\s+a\s+tracked\s+task\b",
    re.I,
)

# Phase 1.1 — project-direction and capability templates (see deterministic.py)
from aethos_core.chat.deterministic import match_project_template  # noqa: E402


def is_ultra_fast_prompt(text: str) -> bool:
    raw = (text or "").strip()
    if not raw:
        return False
    if raw.lower() in _GREETINGS:
        return True
    if _CAPABILITY_RX.search(raw) and len(raw) < 200:
        return True
    return False


def _multi_agent_lane(text: str) -> bool:
    from aethos_core.agents.runtime.planner import is_multi_agent_request

    return is_multi_agent_request((text or "").strip())


def _engineering_intelligence_lane(text: str) -> bool:
    from aethos_core.chat.engineering_intelligence import is_engineering_intelligence_request

    return is_engineering_intelligence_request((text or "").strip())


def _browser_observation_lane(text: str) -> bool:
    from aethos_core.browser_observation.browser_observation_router import is_browser_observation_lane_intent

    return is_browser_observation_lane_intent((text or "").strip())


def _browser_evidence_lane(text: str) -> bool:
    from aethos_core.browser.runtime.browser_evidence_intents import is_browser_evidence_request

    return is_browser_evidence_request((text or "").strip())


def _web_intelligence_lane(text: str) -> bool:
    from aethos_core.chat.web_intelligence import is_web_intelligence_request

    return is_web_intelligence_request((text or "").strip())


def _operational_browser_lane(text: str) -> bool:
    from aethos_core.runtime.browser_intents import is_operational_browser_intent

    return is_operational_browser_intent((text or "").strip())


def _mutation_preflight_lane(text: str) -> bool:
    from aethos_core.chat.mutation_preflight_prompts import create_mutation_preflight_job_reply

    return create_mutation_preflight_job_reply(text) is not None


def _operation_preflight_lane(text: str) -> bool:
    from aethos_core.operations.intents import infer_operation_preflight_intent

    return infer_operation_preflight_intent((text or "").strip()) is not None


def _railway_inventory_lane(text: str) -> bool:
    from aethos_core.runtime.railway_readonly_jobs import is_railway_inventory_request

    return is_railway_inventory_request((text or "").strip())


def _github_inventory_lane(text: str) -> bool:
    from aethos_core.runtime.github_readonly_jobs import is_github_inventory_request

    return is_github_inventory_request((text or "").strip())


def _mutation_target_lane(text: str) -> bool:
    from aethos_core.chat.mutation_target_chat import compose_target_update_reply, compose_why_not_approvable_reply

    return compose_why_not_approvable_reply(text) is not None or compose_target_update_reply(text) is not None


def _mutation_execution_truth_lane(text: str) -> bool:
    from aethos_core.chat.mutation_execution_chat import is_mutation_execution_truth_intent

    return is_mutation_execution_truth_intent(text)


def should_bypass_provider_stream(text: str) -> bool:
    raw = (text or "").strip()
    if not raw:
        return False
    if _multi_agent_lane(raw):
        return True
    if _engineering_intelligence_lane(raw):
        return True
    if _railway_inventory_lane(raw):
        return True
    if _github_inventory_lane(raw):
        return True
    if _mutation_preflight_lane(raw):
        return True
    if _mutation_target_lane(raw):
        return True
    if _mutation_execution_truth_lane(raw):
        return True
    if _browser_observation_lane(raw):
        return True
    if _browser_evidence_lane(raw):
        return True
    if _web_intelligence_lane(raw):
        return True
    if _operation_preflight_lane(raw):
        return True
    if _operational_browser_lane(raw):
        return True
    if _CAPABILITY_RX.search(raw) and len(raw) < 200:
        return True
    if _RUNTIME_MUTATION_RX.search(raw):
        return True
    if is_runtime_config_lane(raw):
        return True
    if _RUNTIME_STATUS_RX.search(raw):
        return True
    if _NEED_FROM_ME_RX.search(raw):
        return True
    if _SETUP_RX.search(raw) and len(raw) < 220:
        return True
    if _WEBSITE_LOGIN_RX.search(raw):
        return True
    if _VERCEL_RX.search(raw) and (
        _LOGIN_RX.search(raw) or _HEALTH_RX.search(raw) or _TERMINAL_VERCEL_RX.search(raw)
    ):
        return True
    if _PUBLIC_STATUS_RX.search(raw):
        return True
    if _DEPLOY_VERCEL_RX.search(raw):
        return True
    if _TERMINAL_ACCESS_RX.search(raw):
        return True
    if _TERMINAL_PROBE_RX.search(raw):
        return True
    if _VERCEL_CLI_PROBE_RX.search(raw):
        return True
    if _ENABLE_BROWSER_RX.search(raw) or _ENABLE_HOST_RX.search(raw):
        return True
    if _BROWSER_INTENT_RX.search(raw):
        return True
    if _ACTION_STATUS_RX.search(raw):
        return True
    if _JOB_STATUS_RX.search(raw):
        return True
    if _EXTERNAL_HEALTH_RX.search(raw):
        return True
    if _PROVIDER_JOB_RX.search(raw):
        return True
    if _QUEUED_TRACKED_JOB_RX.search(raw):
        return True
    if _TRACKED_JOB_RX.search(raw):
        return True
    if _TERMINAL_VERCEL_RX.search(raw):
        return True
    if _LOGIN_RX.search(raw) and re.search(r"https?://|\.com\b", raw, re.I):
        return True
    return False


def is_project_template_lane(text: str, *, session_id: str = "default") -> bool:
    from aethos_core.providers.github.workflow_discovery.workflow_discovery_followup_router import (
        workflow_discovery_preemption_blocks_route,
    )

    raw = (text or "").strip()
    if workflow_discovery_preemption_blocks_route(raw, session_id=session_id):
        return True
    return match_project_template(raw, session_id=session_id) is not None


def is_deterministic_lane(text: str, *, session_id: str = "default") -> bool:
    raw = (text or "").strip()
    if not raw:
        return False
    if _multi_agent_lane(raw):
        return True
    if _engineering_intelligence_lane(raw):
        return True
    if is_ultra_fast_prompt(raw):
        return True
    if should_bypass_provider_stream(raw):
        return True
    if is_project_template_lane(raw, session_id=session_id):
        return True
    return False

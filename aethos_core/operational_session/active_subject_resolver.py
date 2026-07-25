# SPDX-License-Identifier: Apache-2.0
"""Active subject resolution — explicit mention beats session memory."""

from __future__ import annotations

import re
from dataclasses import dataclass

from aethos_core.operational_session.operational_session import OperationalSession, load_operational_session
from aethos_core.operational_session.session_subject import SessionSubject

_RAILWAY_RX = re.compile(r"\brailway\b", re.I)
_VERCEL_RX = re.compile(r"\bvercel\b", re.I)
_SERVICE_HINT_RX = re.compile(
    r"\b(?:for|about|on)\s+(?:the\s+)?([a-z0-9][a-z0-9._-]+)\b"
    r"|\bwhat about (?:the )?([a-z0-9][a-z0-9._-]+)\b"
    r"|\b([a-z0-9]+[-_.][a-z0-9][a-z0-9._-]+)\b",
    re.I,
)
_LOG_TARGET_RX = re.compile(
    r"\b(?:show\s+)?(?:top\s+\d+\s+)?logs?\s+for\s+(?:the\s+)?([a-z0-9][a-z0-9._-]+)\b",
    re.I,
)
_AETHOS_SERVICE_RX = re.compile(r"\b(aethos[-\w]*|pilotos[-\w]*)\b", re.I)
# Quantifiers/pronouns that refer to the previous turn's entities (e.g. "both"
# → the two services just discussed) — never literal project/service names.
_QUANTIFIER_TARGETS = frozenset(
    {"both", "them", "those", "these", "all", "it", "everything", "every", "each"}
)
_QUANTIFIER_RX = re.compile(
    r"\b(for\s+each|both(?:\s+services?)?|all(?:\s+(?:the\s+)?services?)?|them|those|these)\b",
    re.I,
)


@dataclass(frozen=True)
class ResolvedSubject:
    subject: SessionSubject
    source: str
    needs_clarification: bool = False
    clarification_prompt: str = ""


def resolve_active_subject(text: str, *, session_id: str = "default") -> ResolvedSubject:
    raw = (text or "").strip()
    session = load_operational_session(session_id=session_id)

    explicit = _resolve_explicit(raw)
    if explicit is not None:
        merged = _merge_with_session(explicit, session)
        return ResolvedSubject(subject=merged, source=merged.subject_source or "explicit")

    if session.has_active_subject():
        inherited = _inherit_from_session(raw, session)
        if inherited is not None:
            return ResolvedSubject(subject=inherited, source="session")

    registry = _resolve_registry(raw)
    if registry is not None:
        return ResolvedSubject(subject=registry, source="registry")

    return ResolvedSubject(
        subject=SessionSubject(),
        source="none",
        needs_clarification=True,
        clarification_prompt=(
            "Which provider and project should I inspect?\n\n"
            "Example: `show Railway projects` or `top 5 logs for killit on Vercel`."
        ),
    )


def _resolve_explicit(text: str) -> SessionSubject | None:
    from aethos_core.operational_target_resolution.explicit_target_resolver import resolve_explicit_operational_target

    explicit = resolve_explicit_operational_target(text)
    if explicit is not None and (explicit.has_diagnostic_intent or explicit.provider):
        provider = explicit.provider or ("vercel" if explicit.vercel_project else "")
        services = _extract_service_hints(text)
        service = explicit.service or (services[0] if len(services) == 1 else "")
        if not services and service:
            services = [service]
        if explicit.provider == "railway":
            return SessionSubject(
                provider="railway",
                project=explicit.project or "",
                service=service,
                environment=explicit.environment or "staging",
                vercel_project="",
                repo=explicit.repo or "",
                alias=explicit.alias or "",
                target_id=explicit.target_id or "",
                services=services or ([service] if service else []),
                subject_source="explicit",
            )
        return SessionSubject(
            provider=provider,
            project=explicit.project or "",
            service=service,
            environment=explicit.environment or "staging",
            vercel_project=explicit.vercel_project or "",
            repo=explicit.repo or "",
            alias=explicit.alias or "",
            target_id=explicit.target_id or "",
            services=services or ([service] if service else []),
            subject_source="explicit",
        )

    provider = ""
    if _RAILWAY_RX.search(text):
        provider = "railway"
    elif _VERCEL_RX.search(text):
        provider = "vercel"

    what_about = re.search(r"\bwhat about (?:the )?([a-z0-9][a-z0-9._-]+)\b", text, re.I)
    if what_about:
        token = what_about.group(1).strip().lower()
        if token in {"api", "ui"}:
            service = f"aethos-{token}"
            return SessionSubject(
                provider="railway",
                service=service,
                services=[service],
                environment="production",
                subject_source="explicit",
            )
        return SessionSubject(
            provider=provider or "railway",
            service=token,
            services=[token],
            vercel_project=token if provider == "vercel" else "",
            project=token if provider == "railway" else "",
            environment="production" if provider == "railway" else "production",
            subject_source="explicit",
        )

    services = _extract_service_hints(text)
    named_log_target = _extract_named_log_target(text)
    if named_log_target:
        services = [named_log_target]
    if provider or services:
        named = services[0] if len(services) == 1 else ""
        return SessionSubject(
            provider=provider,
            services=services,
            service=named,
            vercel_project="" if provider == "railway" else (named if named and not provider else ""),
            project=named if named and not provider else "",
            environment="staging" if provider == "railway" else "production",
            subject_source="explicit",
        )
    return None


def _resolve_registry(text: str) -> SessionSubject | None:
    from aethos_core.deployment_targets.registry import match_aliases_in_text

    row = match_aliases_in_text(text)
    if row is None:
        return None
    alias = str(row.get("alias") or "")
    vercel_project = str(row.get("vercel_project") or alias or "")
    railway_project = str(row.get("railway_project") or "")
    railway_service = str(row.get("railway_service") or "")
    default_provider = str(row.get("default_provider") or "").lower()
    provider = default_provider
    if _VERCEL_RX.search(text):
        provider = "vercel"
    elif _RAILWAY_RX.search(text):
        provider = "railway"
    elif not provider:
        provider = "vercel" if vercel_project and not railway_project else "railway" if railway_project else "vercel"

    return SessionSubject(
        provider=provider,
        alias=alias,
        target_id=str(row.get("target_id") or ""),
        repo=str(row.get("repo") or ""),
        vercel_project=vercel_project,
        project=railway_project or vercel_project or alias,
        service=railway_service,
        environment=str(row.get("railway_environment") or "production"),
        subject_source="registry",
    )


def _inherit_from_session(text: str, session: OperationalSession) -> SessionSubject | None:
    subject = SessionSubject.from_dict(session.subject.to_dict())
    subject.subject_source = "session"

    services = _extract_service_hints(text)
    if services:
        subject.services = services
        if len(services) == 1:
            subject.service = services[0]
        return subject

    what_about = re.search(r"\bwhat about (?:the )?([a-z0-9][a-z0-9._-]+)\b", text, re.I)
    if what_about:
        token = what_about.group(1).strip().lower()
        if token in {"api", "ui"} and subject.provider == "railway":
            subject.service = f"aethos-{token}"
            subject.services = [subject.service]
        else:
            subject.service = token
            subject.services = [token]
        return subject

    # §4 — "both"/"them"/"those"/"all"/"for each" inherit the prior turn's
    # entities. Prefer the services already on the session subject; otherwise fall
    # back to the standard Railway pair so a follow-up never loses the targets.
    if _QUANTIFIER_RX.search(text) and subject.provider == "railway":
        existing = [s for s in (subject.services or []) if s]
        subject.services = existing if len(existing) >= 2 else ["aethos-api", "aethos-ui"]
        subject.service = ""
        return subject

    return subject


def _merge_with_session(explicit: SessionSubject, session: OperationalSession) -> SessionSubject:
    merged = SessionSubject.from_dict(explicit.to_dict())

    if merged.services or merged.service:
        if merged.provider == "railway":
            merged.vercel_project = ""
            return merged
        if not merged.provider:
            named = merged.service or (merged.services[0] if merged.services else "")
            if named:
                merged.vercel_project = named
                merged.project = named
            return merged

    if not merged.provider and session.subject.provider:
        merged.provider = session.subject.provider
    if not merged.project and session.subject.project:
        merged.project = session.subject.project
    if not merged.environment and session.subject.environment:
        merged.environment = session.subject.environment
    if not merged.vercel_project and session.subject.vercel_project:
        merged.vercel_project = session.subject.vercel_project
    if not merged.service and not merged.services and session.subject.service:
        merged.service = session.subject.service
    if not merged.services and session.subject.services:
        merged.services = list(session.subject.services)
    return merged


def _extract_service_hints(text: str) -> list[str]:
    named = _extract_named_log_target(text)
    if named:
        return [named]
    from aethos_core.operational_session.railway_service_hints import extract_railway_service_hints

    services = extract_railway_service_hints(text)
    if services:
        return services
    found: list[str] = []
    for match in _AETHOS_SERVICE_RX.finditer(text or ""):
        token = match.group(1).lower()
        if token not in found:
            found.append(token)
    return found


def _extract_named_log_target(text: str) -> str:
    match = _LOG_TARGET_RX.search(text or "")
    if not match:
        return ""
    token = match.group(1).strip().lower()
    # Quantifiers/pronouns ("both", "them", "those", "all", …) are never literal
    # project/service names — they refer to the prior turn's entities and must be
    # resolved from session context, not searched for as a provider project.
    if token in _QUANTIFIER_TARGETS:
        return ""
    if token in {"each", "railway", "vercel", "api", "ui", "service", "project"}:
        return ""
    return token

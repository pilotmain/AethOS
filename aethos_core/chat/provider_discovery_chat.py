# SPDX-License-Identifier: Apache-2.0
"""Provider discovery chat — inventory listing and discovery-first diagnosis."""

from __future__ import annotations

import re

from aethos_core.mission_control.visible_navigation_registry import resolve_visible_navigation_path, INTERNAL_SURFACE_MUTATION_APPROVAL

_INVENTORY_RX = re.compile(
    r"\b(what\s+railway\s+services\s+do\s+i\s+have|list\s+railway\s+services|show\s+railway\s+services|railway\s+inventory)\b",
    re.I,
)
_WHY_FAILING_RX = re.compile(
    r"\bwhy\s+(?:is|did)\s+(?:the\s+)?(?:railway\s+)?([a-z0-9][a-z0-9._-]*(?:\s+[a-z0-9][a-z0-9._-]*)*)\s+(?:failing|fail|down)\b",
    re.I,
)
_CHECK_LOGS_RX = re.compile(r"\b(check\s+logs|show\s+logs|read\s+logs)\b.*\b(for\s+)?([a-z0-9][a-z0-9._-]+)?", re.I)


def is_provider_discovery_intent(text: str) -> bool:
    t = text or ""
    return bool(_INVENTORY_RX.search(t) or _WHY_FAILING_RX.search(t) or _CHECK_LOGS_RX.search(t))


def _runtime_path() -> str:
    return resolve_visible_navigation_path(internal_surface=INTERNAL_SURFACE_MUTATION_APPROVAL, mode="operator")


def _format_inventory_list(inventory) -> str:
    lines: list[str] = []
    idx = 1
    for project in inventory.projects:
        for environment in project.environments:
            header = f"**{project.name} / {environment.name}**"
            if header not in lines:
                lines.append(header)
            for service in environment.services:
                domain = f" — domain: {service.domain}" if service.domain else ""
                lines.append(f"{idx}. {service.name} — {service.status}{domain}")
                idx += 1
    return "\n".join(lines) if lines else "No Railway services discovered yet."


def compose_provider_discovery_reply(text: str, *, session_id: str = "default") -> tuple[str, str, dict[str, str]] | None:
    from aethos_core.chat.operational_master_router import master_router_has_priority_route

    if master_router_has_priority_route(text, session_id=session_id):
        return None

    if not is_provider_discovery_intent(text):
        return None

    if _INVENTORY_RX.search(text):
        from aethos_core.provider_discovery.discovery_runtime import get_provider_inventory

        inventory = get_provider_inventory(provider="railway")
        if not inventory.projects:
            return (
                "I need to refresh Railway inventory before listing services.\n\n"
                "Check **Provider status** or ensure Railway credentials are configured.",
                "provider_discovery_inventory",
                {},
            )
        body = "I found these Railway services:\n\n" + _format_inventory_list(inventory)
        return (body, "provider_discovery_inventory", {"provider": "railway"})

    if _WHY_FAILING_RX.search(text):
        from aethos_core.approval.session_scopes import has_readonly_railway_scope
        from aethos_core.operations.devops_loop import run_devops_loop
        from aethos_core.provider_discovery.discovery_runtime import get_provider_inventory
        from aethos_core.provider_discovery.target_resolution import extract_service_phrase, resolve_target_from_inventory

        inventory = get_provider_inventory(provider="railway")
        phrase = extract_service_phrase(text) or "api"
        resolution = resolve_target_from_inventory(inventory=inventory, user_request=text, target_hints=[phrase])
        if not resolution.resolved:
            return (
                f"I couldn't resolve a Railway service target for **{phrase}**.\n\n"
                "Say **What Railway services do I have?** first.\n\n"
                "No mutation has been performed.",
                "provider_discovery_diagnosis",
                {},
            )
        target_path = f"{resolution.project_name} / {resolution.environment} / {resolution.service_name}"
        loop = run_devops_loop(
            provider="railway",
            service_name=str(resolution.service_name or ""),
            project_name=resolution.project_name,
            environment=resolution.environment,
            phase="diagnose",
        )
        diagnosis = loop.get("diagnosis") or {}
        fix = loop.get("fix_plan") or {}
        if not diagnosis.get("ok"):
            return (
                f"I checked **{target_path}**, but log evidence is insufficient to diagnose yet.",
                "provider_discovery_diagnosis",
                {"service_name": str(resolution.service_name or "")},
            )
        signals = diagnosis.get("log_signals") or []
        signal_lines = "\n".join(f"- {s}" for s in signals[:3]) if signals else "- runtime errors in recent logs"
        fix_summary = fix.get("summary") or "Prepare a governed fix plan."
        readonly_note = (
            "\n\n(Readonly Railway checks are allowed for this session.)" if has_readonly_railway_scope(session_id=session_id) else ""
        )
        return (
            f"I checked deployment status and recent logs for **{target_path}**.\n\n"
            f"The service may be online, but logs indicate:\n{signal_lines}\n\n"
            f"Most likely cause:\n- {diagnosis.get('likely_cause')}\n\n"
            f"Recommended fix:\n- {fix_summary}\n\n"
            f"I can prepare a governed fix plan before changing anything.{readonly_note}",
            "provider_discovery_diagnosis",
            {"service_name": str(resolution.service_name or ""), "category": str(diagnosis.get("category") or "")},
        )

    if _CHECK_LOGS_RX.search(text):
        from aethos_core.provider_discovery.discovery_runtime import get_provider_inventory
        from aethos_core.provider_discovery.target_resolution import extract_service_phrase, resolve_target_from_inventory
        from aethos_core.providers.railway.cli_executor import railway_logs

        inventory = get_provider_inventory(provider="railway")
        match = _CHECK_LOGS_RX.search(text)
        phrase = (match.group(2) if match else None) or extract_service_phrase(text) or "api"
        resolution = resolve_target_from_inventory(inventory=inventory, user_request=text, target_hints=[phrase])
        if not resolution.resolved:
            return (
                f"I couldn't resolve Railway service **{phrase}** for log inspection.",
                "provider_discovery_logs",
                {},
            )
        logs = list((railway_logs(service_name=str(resolution.service_name or "")).get("logs") or [])[-5:])
        if not logs:
            return (
                f"No recent Railway log excerpts stored for **{resolution.service_name}** yet.",
                "provider_discovery_logs",
                {"service_name": str(resolution.service_name or "")},
            )
        lines = [f"- {str(row.get('message') or row)[:200]}" for row in logs]
        return (
            f"Recent Railway logs for **{resolution.project_name} / {resolution.environment} / {resolution.service_name}**:\n\n"
            + "\n".join(lines),
            "provider_discovery_logs",
            {"service_name": str(resolution.service_name or "")},
        )

    return None

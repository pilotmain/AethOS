# SPDX-License-Identifier: Apache-2.0
"""Operation planning through provider skills."""

from __future__ import annotations

from typing import Any

from aethos_core.operational_skill_runtime.skill_registry import resolve_skill_for_provider


def plan_operation(
    *,
    provider: str,
    operation: str,
    target: Any,
    context: dict[str, Any] | None = None,
) -> dict[str, Any]:
    skill, err = resolve_skill_for_provider(provider)
    if skill is None:
        return {"ok": False, "error": err}
    plan = skill.plan(operation=operation, target=target, context=context)
    dry = skill.dry_run(plan)
    return {"ok": dry.ok, "plan": plan.to_dict(), "dry_run": dry.to_dict(), "provider": provider}

# SPDX-License-Identifier: Apache-2.0
"""FIX 115 — static rollback isolation audit (no mutations)."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

_SECRET_PATTERNS = (
    re.compile(r"sk-[a-zA-Z0-9]{10,}"),
    re.compile(r"rw_[a-zA-Z0-9]{10,}"),
    re.compile(r"ghp_[a-zA-Z0-9]{10,}"),
)


@dataclass(frozen=True)
class RollbackIsolationAudit:
    ok: bool
    rollback_executor_does_not_import_forward_executor: bool
    rollback_env_adapter_has_no_deploy_trigger: bool
    rollback_receipts_have_no_secret_values: bool
    rollback_idempotency_enforced: bool
    rollback_respects_kill_switch: bool
    rollback_staging_only_enforced: bool
    checks: list[dict[str, Any]] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "ok": self.ok,
            "checks": list(self.checks),
        }


def _read_module_source(module_name: str) -> str:
    import sys

    mod = sys.modules.get(module_name)
    if mod and getattr(mod, "__file__", None):
        return Path(mod.__file__).read_text(encoding="utf-8")
    return ""


def build_rollback_isolation_audit(*, execution_id: str = "") -> RollbackIsolationAudit:
    _ = execution_id
    dispatch_src = _read_module_source(
        "aethos_core.providers.railway.execution_contract.execution_live_rollback_dispatch"
    )
    env_exec_src = _read_module_source(
        "aethos_core.providers.railway.execution_contract.execution_real_rollback_env_configure"
    )
    env_adapter_src = _read_module_source(
        "aethos_core.providers.railway.greenfield_adapters.revert_env_configure_adapter"
    )
    disconnect_src = _read_module_source(
        "aethos_core.providers.railway.execution_contract.execution_real_rollback_disconnect_executor"
    )

    no_forward_import = all(
        token not in src
        for src in (dispatch_src, env_exec_src, disconnect_src)
        for token in (
            "execution_real_mutation_dispatch",
            "run_single_real_mutation_phase",
            "execution_dry_run_executor",
            "trigger_railway_deploy",
            "trigger_deploy_adapter",
        )
    )

    no_deploy_trigger = all(
        token not in env_adapter_src
        for token in (
            "trigger_railway_deploy",
            "trigger_deploy",
            "serviceInstanceRedeploy",
        )
    )

    receipts_clean = True
    if execution_id:
        from aethos_core.providers.railway.execution_contract.execution_receipts import (
            list_rollback_receipts,
        )

        for receipt in list_rollback_receipts(execution_id=execution_id):
            blob = str(receipt)
            if any(pat.search(blob) for pat in _SECRET_PATTERNS):
                receipts_clean = False
                break
            for value in receipt.get("env_var_names") or []:
                if "=" in str(value):
                    receipts_clean = False

    idempotency_enforced = "rollback_phase_recorded" in dispatch_src and "idempotent_replay" in env_exec_src
    kill_switch = (
        "is_railway_mutation_kill_switch_active" in dispatch_src
        or "is_railway_mutation_kill_switch_active" in env_exec_src
        or "allows_disconnect_source_rollback" in dispatch_src
    )
    staging_only = (
        "assess_railway_rollback_readiness" in dispatch_src
        and "is_rollback_blocked_environment" in env_exec_src
        and "is_rollback_blocked_environment" in disconnect_src
    )

    checks = [
        {
            "name": "rollback_executor_does_not_import_forward_executor",
            "pass": no_forward_import,
        },
        {
            "name": "rollback_env_adapter_has_no_deploy_trigger",
            "pass": no_deploy_trigger,
        },
        {
            "name": "rollback_receipts_have_no_secret_values",
            "pass": receipts_clean,
        },
        {
            "name": "rollback_idempotency_enforced",
            "pass": idempotency_enforced,
        },
        {
            "name": "rollback_respects_kill_switch",
            "pass": kill_switch,
        },
        {
            "name": "rollback_staging_only_enforced",
            "pass": staging_only,
        },
    ]
    ok = all(row["pass"] for row in checks)
    return RollbackIsolationAudit(
        ok=ok,
        rollback_executor_does_not_import_forward_executor=no_forward_import,
        rollback_env_adapter_has_no_deploy_trigger=no_deploy_trigger,
        rollback_receipts_have_no_secret_values=receipts_clean,
        rollback_idempotency_enforced=idempotency_enforced,
        rollback_respects_kill_switch=kill_switch,
        rollback_staging_only_enforced=staging_only,
        checks=checks,
    )


def render_rollback_isolation_audit(audit: RollbackIsolationAudit) -> str:
    lines = [
        "# Railway Rollback Audit",
        "",
        f"- audit_ok: **{str(audit.ok).lower()}**",
        "",
        "Isolation checks:",
    ]
    for row in audit.checks:
        status = "pass" if row.get("pass") else "fail"
        lines.append(f"- {row.get('name')}: **{status}**")
    lines.extend(
        [
            "",
            "No rollback mutation performed by this audit command.",
        ]
    )
    return "\n".join(lines)

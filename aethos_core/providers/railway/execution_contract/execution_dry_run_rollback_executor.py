# SPDX-License-Identifier: Apache-2.0
"""
FIX 110 — Dry-run rollback executor for connect_source (disconnect_repo_source).

Never calls live rollback adapters (FIX 111). Never performs env writes or deploy triggers.
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any

from aethos_core.providers.railway.execution_contract.connect_source_rollback_contract import (
    build_connect_source_rollback_contract,
)
from aethos_core.providers.railway.execution_contract.execution_journal import save_execution_journal
from aethos_core.providers.railway.execution_contract.execution_receipt_status import (
    STATUS_ROLLBACK_SIMULATED_FAILURE,
    STATUS_ROLLBACK_SIMULATED_SKIPPED,
    STATUS_ROLLBACK_SIMULATED_SUCCESS,
    rollback_phase_recorded,
)
from aethos_core.providers.railway.execution_contract.execution_receipts import (
    find_phase_receipt,
    record_execution_receipt,
)
from aethos_core.providers.railway.execution_contract.execution_rollback import journal_rollback_phase
from aethos_core.providers.railway.execution_contract.execution_rollback_contract_models import (
    CONNECT_SOURCE_ROLLBACK_ACTION,
    CONNECT_SOURCE_ROLLBACK_PHASE,
)


@dataclass
class DryRunConnectSourceRollbackResult:
    journal: dict[str, Any]
    mutation_performed: bool = False
    idempotent_replay: bool = False
    rollback_receipt_recorded: bool = False
    detail: str = ""
    errors: list[str] = field(default_factory=list)


def _record_rollback_receipt(
    *,
    execution_id: str,
    status: str,
    detail: str,
    replayed: bool = False,
) -> dict[str, Any]:
    started = datetime.now(UTC)
    started_mono = time.monotonic()
    duration_ms = max(int((time.monotonic() - started_mono) * 1000), 1)
    completed = datetime.now(UTC)
    return record_execution_receipt(
        execution_id=execution_id,
        phase=CONNECT_SOURCE_ROLLBACK_PHASE,
        status=status,
        mutation_performed=False,
        detail=detail,
        started_at=started.isoformat(),
        completed_at=completed.isoformat(),
        duration_ms=duration_ms,
        replayed=replayed,
        skipped_existing=replayed,
    )


def run_dry_run_connect_source_rollback(
    *,
    journal: dict[str, Any],
    plan: dict[str, Any] | None = None,
) -> DryRunConnectSourceRollbackResult:
    """
    Simulate disconnect_repo_source rollback for connect_source binding.

    Does not call Railway APIs or any live mutation/rollback adapter.
    """
    _ = plan
    execution_id = str(journal.get("execution_id") or "")
    if not execution_id:
        return DryRunConnectSourceRollbackResult(
            journal=journal,
            detail="No execution_id on journal.",
            errors=["execution_id_missing"],
        )

    contract = build_connect_source_rollback_contract(
        plan=plan,
        journal=journal,
        execution_id=execution_id,
    )

    existing = find_phase_receipt(execution_id=execution_id, phase=CONNECT_SOURCE_ROLLBACK_PHASE)
    if rollback_phase_recorded(existing):
        journal["connect_source_rollback_simulated"] = True
        journal["execution_mode"] = str(journal.get("execution_mode") or "dry_run_rollback")
        journal = save_execution_journal(journal)
        return DryRunConnectSourceRollbackResult(
            journal=journal,
            idempotent_replay=True,
            rollback_receipt_recorded=True,
            detail="rollback_connect_source already simulated; idempotent replay.",
        )

    if not contract.eligible_for_dry_run_rollback:
        receipt = _record_rollback_receipt(
            execution_id=execution_id,
            status=STATUS_ROLLBACK_SIMULATED_FAILURE,
            detail="; ".join(contract.blocker_messages) or "rollback not eligible",
        )
        journal["rollback_last_receipt_id"] = str(receipt.get("receipt_id") or "")
        journal = save_execution_journal(journal)
        return DryRunConnectSourceRollbackResult(
            journal=journal,
            detail="connect_source rollback simulation blocked.",
            errors=list(contract.blockers),
        )

    # Prove dry-run path never imports live disconnect adapter.
    _assert_no_live_rollback_adapter_import()

    binding = journal.get("github_source_bound") if isinstance(journal.get("github_source_bound"), dict) else {}
    repo = contract.repository
    branch = contract.branch
    detail = (
        f"dry_run rollback: simulate {CONNECT_SOURCE_ROLLBACK_ACTION} for "
        f"`{repo}@{branch}` (no Railway API call; FIX 111 enables live disconnect)."
    )

    receipt = _record_rollback_receipt(
        execution_id=execution_id,
        status=STATUS_ROLLBACK_SIMULATED_SUCCESS,
        detail=detail,
    )

    rollback_journal = journal.get("rollback_journal")
    if isinstance(rollback_journal, dict):
        updated_rollback = journal_rollback_phase(
            rollback_journal,
            action=CONNECT_SOURCE_ROLLBACK_ACTION,
            status="simulated",
            detail=f"Simulated disconnect of `{repo}@{branch}` (dry_run only).",
        )
        for row in list(updated_rollback.get("actions") or []):
            if str(row.get("action") or "") == CONNECT_SOURCE_ROLLBACK_ACTION:
                row["status"] = "simulated"
                row["mutation_performed"] = False
        journal["rollback_journal"] = updated_rollback

    journal["connect_source_rollback_simulated"] = True
    journal["connect_source_rollback_mode"] = "dry_run"
    journal["github_source_bound_rollback"] = dict(binding) if binding else {
        "repository": repo,
        "branch": branch,
    }
    journal["rollback_last_receipt_id"] = str(receipt.get("receipt_id") or "")
    journal["rollback_available"] = True
    journal = save_execution_journal(journal)

    return DryRunConnectSourceRollbackResult(
        journal=journal,
        mutation_performed=False,
        rollback_receipt_recorded=True,
        detail=detail,
    )


def _assert_no_live_rollback_adapter_import() -> None:
    import re
    import sys

    dry_mod = sys.modules[__name__]
    source = open(dry_mod.__file__, encoding="utf-8").read()
    if re.search(
        r"^\s*(?:from|import)\s+.*disconnect_github_source",
        source,
        re.MULTILINE,
    ):
        raise RuntimeError("dry-run rollback executor must not import live disconnect adapter")

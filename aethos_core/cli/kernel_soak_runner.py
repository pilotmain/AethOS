# SPDX-License-Identifier: Apache-2.0
"""Automated live kernel soak — operational turns + optional daily snapshots."""

from __future__ import annotations

import argparse
import json
import sys
import time
from dataclasses import asdict, dataclass, field
from datetime import UTC, datetime, timedelta
from typing import Any

# (scenario_id, session_suffix, prompts)
SOAK_SCENARIOS: tuple[tuple[str, str, tuple[str, ...]], ...] = (
    ("railway-inventory", "rail", ("show Railway projects",)),
    (
        "railway-logs-followup",
        "rail-logs",
        ("show Railway projects", "show logs", "top 5 only", "what about api?"),
    ),
    ("railway-health", "rail-health", ("check health for aethos-api on railway",)),
    ("railway-deployment", "rail-deploy", ("show deployment status on railway",)),
    (
        "railway-recovery",
        "rail-recovery",
        ("killit on railway", "missing service foo-bar on railway"),
    ),
    ("vercel-inventory", "ver", ("show vercel projects",)),
    (
        "vercel-logs-followup",
        "ver-logs",
        ("give me top 5 logs for killit", "can you give me that?"),
    ),
    ("vercel-deployments", "ver-deploy", ("list vercel deployments for killit",)),
    ("vercel-health", "ver-health", ("check health for killit on vercel",)),
    ("vercel-status", "ver-status", ("deployment status for killit on vercel",)),
)


@dataclass
class SoakTurnResult:
    scenario_id: str
    prompt: str
    session_id: str
    ok: bool
    intent: str
    reply_preview: str = ""
    error: str = ""


@dataclass
class SoakBatchResult:
    batch_id: str
    started_at: float
    finished_at: float = 0.0
    turns: list[SoakTurnResult] = field(default_factory=list)
    acceptance: dict[str, Any] = field(default_factory=dict)
    soak_progress: dict[str, Any] = field(default_factory=dict)
    provider_proof: dict[str, Any] = field(default_factory=dict)

    @property
    def ok_count(self) -> int:
        return sum(1 for row in self.turns if row.ok)

    @property
    def total(self) -> int:
        return len(self.turns)


def _bootstrap() -> None:
    from aethos_core.operational_skill_runtime import bootstrap_operational_runtime

    bootstrap_operational_runtime(force=False)


def _run_prompt(*, prompt: str, session_id: str) -> SoakTurnResult:
    from aethos_core.operational_session.operational_runtime import run_operational_turn

    turn = run_operational_turn(prompt, session_id=session_id, channel="cli")
    preview = (turn.reply or "").replace("\n", " ")[:180]
    return SoakTurnResult(
        scenario_id="",
        prompt=prompt,
        session_id=session_id,
        ok=bool(turn.ok),
        intent=str(turn.intent or ""),
        reply_preview=preview,
        error="" if turn.ok else preview,
    )


def run_soak_batch(*, batch_id: str, session_prefix: str = "soak-auto") -> SoakBatchResult:
    _bootstrap()
    started = time.time()
    batch = SoakBatchResult(batch_id=batch_id, started_at=started)
    for scenario_id, suffix, prompts in SOAK_SCENARIOS:
        session_id = f"{session_prefix}-{suffix}-{batch_id}"
        for prompt in prompts:
            row = _run_prompt(prompt=prompt, session_id=session_id)
            row.scenario_id = scenario_id
            batch.turns.append(row)
            time.sleep(0.15)
    batch.finished_at = time.time()
    batch.acceptance, batch.soak_progress, batch.provider_proof = _acceptance_snapshot()
    return batch


def _acceptance_snapshot() -> tuple[dict[str, Any], dict[str, Any], dict[str, Any]]:
    from aethos_core.cli.kernel_reality_report import cmd_kernel_reality_report
    from io import StringIO
    import contextlib

    buf = StringIO()
    with contextlib.redirect_stdout(buf):
        cmd_kernel_reality_report(["--json"])
    summary = json.loads(buf.getvalue())
    acc = dict(summary.get("acceptance") or {})
    soak = dict(summary.get("soak_progress") or {})
    proof = dict(summary.get("provider_proof") or {})
    return acc, soak, proof


def gates_ready(acceptance: dict[str, Any] | None = None) -> bool:
    acc = acceptance or _acceptance_snapshot()[0]
    return bool(acc.get("ready_for_manual_test") or acc.get("operationally_proven"))


def synthetic_soak_date(*, day_index: int, base: datetime | None = None) -> str:
    """Day 1 = base UTC date, day 2 = base+1, etc."""
    anchor = (base or datetime.now(UTC)).replace(hour=12, minute=0, second=0, microsecond=0)
    return (anchor + timedelta(days=max(0, day_index - 1))).strftime("%Y-%m-%d")


def save_soak_daily(*, as_date: str | None = None) -> dict[str, Any]:
    from aethos_core.cli.kernel_reality_report import cmd_kernel_reality_report

    argv = ["--save-daily", "--json"]
    if as_date:
        argv.extend(["--as-date", as_date])
    from io import StringIO
    import contextlib

    buf = StringIO()
    with contextlib.redirect_stdout(buf):
        code = cmd_kernel_reality_report(argv)
    if code != 0:
        raise RuntimeError("save-daily failed")
    return json.loads(buf.getvalue())


def run_kernel_soak(
    *,
    batch_id: str | None = None,
    session_prefix: str = "soak-auto",
    save_daily: bool = False,
    soak_day_index: int | None = None,
    json_out: bool = False,
) -> dict[str, Any]:
    bid = batch_id or datetime.now(UTC).strftime("%Y%m%d-%H%M%S")
    batch = run_soak_batch(batch_id=bid, session_prefix=session_prefix)

    saved: dict[str, Any] | None = None
    if save_daily:
        as_date = None
        if soak_day_index is not None:
            as_date = synthetic_soak_date(day_index=soak_day_index)
        saved = save_soak_daily(as_date=as_date)
        batch.acceptance, batch.soak_progress, batch.provider_proof = _acceptance_snapshot()

    payload = {
        "batch_id": bid,
        "ok_turns": batch.ok_count,
        "total_turns": batch.total,
        "pass_rate": round(100.0 * batch.ok_count / batch.total, 1) if batch.total else 0.0,
        "ready_for_manual_test": gates_ready(batch.acceptance),
        "acceptance": batch.acceptance,
        "soak_progress": batch.soak_progress,
        "provider_proof": batch.provider_proof,
        "saved_daily": saved is not None,
        "synthetic_date": saved.get("date") if isinstance(saved, dict) else None,
        "turns": [asdict(row) for row in batch.turns],
    }
    if json_out:
        print(json.dumps(payload, indent=2))
    else:
        print(f"Soak batch {bid}: {batch.ok_count}/{batch.total} ok turns")
        print(f"Ready for manual test: {payload['ready_for_manual_test']}")
        if batch.provider_proof:
            rw = (batch.provider_proof.get("railway") or {}).get("successful_turns")
            vw = (batch.provider_proof.get("vercel") or {}).get("successful_turns")
            print(f"Provider proof — railway: {rw}, vercel: {vw}")
        soak = batch.soak_progress or {}
        print(f"Soak days: {soak.get('days_recorded')}/{soak.get('required_days')}")
    return payload


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run live kernel soak batch (chat/CLI parity)")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--batch-id", default=None)
    parser.add_argument("--session-prefix", default="soak-auto")
    parser.add_argument("--save-daily", action="store_true")
    parser.add_argument(
        "--soak-day-index",
        type=int,
        default=None,
        help="When set with --save-daily, stamp snapshot as synthetic day N (requires KERNEL_SOAK_DEV_ACCELERATE=true)",
    )
    parser.add_argument("--check-gates", action="store_true", help="Exit 0 when ready_for_manual_test")
    args = parser.parse_args(argv)

    if args.check_gates:
        acc, soak, _ = _acceptance_snapshot()
        ready = gates_ready(acc)
        if args.json:
            print(json.dumps({"ready_for_manual_test": ready, "acceptance": acc, "soak_progress": soak}, indent=2))
        else:
            print(f"ready_for_manual_test: {ready}")
        return 0 if ready else 1

    payload = run_kernel_soak(
        batch_id=args.batch_id,
        session_prefix=args.session_prefix,
        save_daily=args.save_daily,
        soak_day_index=args.soak_day_index,
        json_out=args.json,
    )
    return 0 if payload.get("ready_for_manual_test") else 0


if __name__ == "__main__":
    sys.exit(main())

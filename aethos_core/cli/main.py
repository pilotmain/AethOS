# SPDX-License-Identifier: Apache-2.0
"""AethOS CLI — doctor and enterprise utilities."""

from __future__ import annotations

import argparse
import json
import sys

from aethos_core.cli.brand import BrandTone, aethos_log, format_banner, format_section, format_status
from aethos_core.cli.operator_cli import OPERATOR_DEFAULT_SESSION_ID


def main() -> None:
    parser = argparse.ArgumentParser(prog="aethos", description="AethOS enterprise CLI")
    sub = parser.add_subparsers(dest="command")

    doctor_p = sub.add_parser("doctor", help="Environment readiness checks")
    doctor_p.add_argument("--json", action="store_true", help="Output JSON")
    doctor_p.add_argument("--category", type=str, default=None, help="Filter by category")
    doctor_p.add_argument("--no-probe", action="store_true", help="Skip HTTP probes")
    doctor_p.add_argument("--probe-browser", action="store_true", help="Probe Playwright launch")

    sub.add_parser("config", help="Show configuration center summary (no secrets)")

    worker_p = sub.add_parser("worker", help="Run standalone worker process")
    worker_p.add_argument("--worker-id", type=str, default=None)

    demo_p = sub.add_parser("demo", help="Demo mode controls")
    demo_p.add_argument("action", choices=["enable", "disable", "status"], nargs="?", default="status")

    sub.add_parser("onboard", help="Operator onboarding checklist")

    gateway_p = sub.add_parser("gateway", help="Run the AethOS API gateway (uvicorn)")
    gateway_p.add_argument("--host", default="127.0.0.1")
    gateway_p.add_argument("--port", type=int, default=8010)
    gateway_p.add_argument("--reload", action="store_true")

    status_p = sub.add_parser("status", help="Gateway health and provider skill snapshot")
    status_p.add_argument("--api-base", default="http://127.0.0.1:8010")

    logs_p = sub.add_parser("logs", help="Tail local runtime artifacts under data/")
    logs_p.add_argument("--category", default=None)
    logs_p.add_argument("--lines", type=int, default=40)

    tunnel_p = sub.add_parser("tunnel", help="Managed ngrok tunnel for Telegram webhooks")
    tunnel_p.add_argument("action", nargs="?", default="status", choices=["start", "stop", "restart", "status"])
    tunnel_p.add_argument("--api-base", default="http://127.0.0.1:8010")

    install_p = sub.add_parser("install-service", help="Print launchd/systemd unit for always-on gateway")
    install_p.add_argument("--host", default="127.0.0.1")
    install_p.add_argument("--port", type=int, default=8010)

    msg_p = sub.add_parser("message", help="Send a message through the chat gateway")
    msg_sub = msg_p.add_subparsers(dest="message_command")
    send_p = msg_sub.add_parser("send", help="POST to deterministic chat endpoint")
    send_p.add_argument("text", nargs="+", help="Message text")
    send_p.add_argument("--session-id", default=OPERATOR_DEFAULT_SESSION_ID)
    send_p.add_argument("--api-base", default="http://127.0.0.1:8010")

    pairing_p = sub.add_parser("pairing", help="Channel Gateway sender pairing/allowlist (handoff §6)")
    pairing_sub = pairing_p.add_subparsers(dest="pairing_command")
    pair_approve = pairing_sub.add_parser("approve", help="Approve a pending sender by pairing code")
    pair_approve.add_argument("channel", help="Channel name e.g. telegram")
    pair_approve.add_argument("code", help="Pairing code shown to the sender")
    pairing_sub.add_parser("list", help="List pending + allowlisted senders")
    pair_revoke = pairing_sub.add_parser("revoke", help="Remove a sender from the allowlist")
    pair_revoke.add_argument("channel", help="Channel name e.g. telegram")
    pair_revoke.add_argument("sender", help="External sender/user id")

    outbound_p = sub.add_parser("outbound", help="Governed outbound message sends (handoff §8)")
    outbound_sub = outbound_p.add_subparsers(dest="outbound_command")
    outbound_sub.add_parser("list", help="List outbound-send preflights and gate status")
    out_approve = outbound_sub.add_parser("approve", help="Approve + send a governed outbound preflight")
    out_approve.add_argument("preflight_id", help="Outbound preflight id e.g. obs-xxxx")

    op_p = sub.add_parser("operational", help="Operational kernel (same runtime as chat)")
    op_p.add_argument("words", nargs=argparse.REMAINDER, help="Operational request text")
    op_p.add_argument("--session-id", default=OPERATOR_DEFAULT_SESSION_ID)
    op_p.add_argument("--json", action="store_true")

    smoke_p = sub.add_parser("kernel-smoke", help="Automated operational kernel smoke certification")
    smoke_p.add_argument("--json", action="store_true")

    reality_p = sub.add_parser("kernel-reality-report", help="Operational kernel reality evidence report")
    reality_p.add_argument("--days", type=int, default=7)
    reality_p.add_argument("--json", action="store_true")
    reality_p.add_argument("--save-daily", action="store_true", help="Record today's snapshot for 7-day soak")
    reality_p.add_argument(
        "--as-date",
        default=None,
        help="Synthetic soak date YYYY-MM-DD (KERNEL_SOAK_DEV_ACCELERATE=true)",
    )

    soak_p = sub.add_parser("kernel-soak", help="Live automated kernel soak batch")
    soak_p.add_argument("--json", action="store_true")
    soak_p.add_argument("--batch-id", default=None)
    soak_p.add_argument("--session-prefix", default="soak-auto")
    soak_p.add_argument("--save-daily", action="store_true")
    soak_p.add_argument("--soak-day-index", type=int, default=None)
    soak_p.add_argument("--check-gates", action="store_true")

    args = parser.parse_args()
    if args.command == "doctor":
        _cmd_doctor(args)
    elif args.command == "config":
        _cmd_config(args)
    elif args.command == "worker":
        from aethos_core.runtime.worker_main import run_worker

        run_worker(worker_id=getattr(args, "worker_id", None))
    elif args.command == "demo":
        _cmd_demo(args)
    elif args.command == "onboard":
        from aethos_core.cli.operator_cli import cmd_onboard

        sys.exit(cmd_onboard())
    elif args.command == "gateway":
        from aethos_core.cli.operator_cli import cmd_gateway

        sys.exit(cmd_gateway(host=args.host, port=args.port, reload=args.reload))
    elif args.command == "status":
        from aethos_core.cli.operator_cli import cmd_status

        sys.exit(cmd_status(api_base=args.api_base))
    elif args.command == "logs":
        from aethos_core.cli.operator_cli import cmd_logs

        sys.exit(cmd_logs(category=args.category, lines=args.lines))
    elif args.command == "tunnel":
        from aethos_core.cli.operator_cli import cmd_tunnel

        sys.exit(cmd_tunnel(action=args.action, api_base=args.api_base))
    elif args.command == "install-service":
        from aethos_core.cli.operator_cli import cmd_install_service

        sys.exit(cmd_install_service(host=args.host, port=args.port))
    elif args.command == "message" and args.message_command == "send":
        from aethos_core.cli.operator_cli import cmd_message_send

        text = " ".join(args.text)
        sys.exit(cmd_message_send(api_base=args.api_base, message=text, session_id=args.session_id))
    elif args.command == "pairing":
        import json as _json

        from aethos_core.channels import pairing_store

        if args.pairing_command == "approve":
            print(_json.dumps(pairing_store.approve_pairing(args.channel, args.code), indent=2))
        elif args.pairing_command == "revoke":
            print(_json.dumps(pairing_store.revoke_sender(args.channel, args.sender), indent=2))
        elif args.pairing_command == "list":
            print(_json.dumps(pairing_store.pairing_status_payload(), indent=2))
        else:
            parser.parse_args(["pairing", "--help"])
        sys.exit(0)
    elif args.command == "outbound":
        import json as _json

        from aethos_core.channels import outbound_governance

        if args.outbound_command == "approve":
            print(_json.dumps(outbound_governance.approve_outbound_send(args.preflight_id), indent=2))
        elif args.outbound_command == "list":
            print(_json.dumps(outbound_governance.outbound_status_payload(), indent=2))
        else:
            parser.parse_args(["outbound", "--help"])
        sys.exit(0)
    elif args.command == "operational":
        from aethos_core.cli.operational_cli import cmd_operational

        op_argv = list(args.words or [])
        if args.session_id != OPERATOR_DEFAULT_SESSION_ID:
            op_argv = ["--session-id", args.session_id] + op_argv
        if args.json:
            op_argv = ["--json"] + op_argv
        sys.exit(cmd_operational(op_argv))
    elif args.command == "kernel-smoke":
        from aethos_core.cli.kernel_smoke_runner import main as smoke_main

        sys.exit(smoke_main(["--json"] if args.json else []))
    elif args.command == "kernel-reality-report":
        from aethos_core.cli.kernel_reality_report import cmd_kernel_reality_report

        argv = []
        if args.days != 7:
            argv.extend(["--days", str(args.days)])
        if args.json:
            argv.append("--json")
        if args.save_daily:
            argv.append("--save-daily")
        if getattr(args, "as_date", None):
            argv.extend(["--as-date", args.as_date])
        sys.exit(cmd_kernel_reality_report(argv))
    elif args.command == "kernel-soak":
        from aethos_core.cli.kernel_soak_runner import main as soak_main

        soak_argv: list[str] = []
        if args.json:
            soak_argv.append("--json")
        if args.batch_id:
            soak_argv.extend(["--batch-id", args.batch_id])
        if args.session_prefix != "soak-auto":
            soak_argv.extend(["--session-prefix", args.session_prefix])
        if args.save_daily:
            soak_argv.append("--save-daily")
        if args.soak_day_index is not None:
            soak_argv.extend(["--soak-day-index", str(args.soak_day_index)])
        if args.check_gates:
            soak_argv.append("--check-gates")
        sys.exit(soak_main(soak_argv))
    else:
        print(format_banner())
        parser.print_help()
        sys.exit(0)


def _cmd_doctor(args: argparse.Namespace) -> None:
    from aethos_core.enterprise.doctor import run_doctor_checks

    result = run_doctor_checks(
        probe_api=not args.no_probe,
        probe_web=not args.no_probe,
        probe_browser=args.probe_browser,
        category=args.category,
    )
    if args.json:
        print(json.dumps(result, indent=2))
    else:
        print(format_banner())
        print(aethos_log("Environment readiness doctor", tone=BrandTone.PRIMARY))
        print(format_status("Overall", str(result.get("overall")), tone=_tone_for_status(str(result.get("overall")))))
        print(format_status("Summary", str(result.get("summary"))))
        print(format_section("Checks"))
        for check in result.get("checks") or []:
            st = str(check.get("status"))
            tone = _tone_for_status(st)
            print(format_status(check.get("name", ""), st, tone=tone))
            print(f"    {check.get('detail')}")
            if check.get("fix_hint"):
                print(f"    Fix: {check['fix_hint']}")
            actionable = check.get("actionable")
            if actionable:
                print(f"    Next: {actionable.get('next_command')}")
    sys.exit(0 if result.get("ok") else 1)


def _cmd_config(args: argparse.Namespace) -> None:
    from aethos_core.enterprise.config_center import build_configuration_center

    data = build_configuration_center()
    print(json.dumps(data, indent=2))


def _cmd_demo(args: argparse.Namespace) -> None:
    from aethos_core.enterprise.demo_mode import demo_status, disable_demo_mode, enable_demo_mode

    if args.action == "enable":
        result = enable_demo_mode()
    elif args.action == "disable":
        result = disable_demo_mode()
    else:
        result = demo_status()
    print(json.dumps(result, indent=2))


def _tone_for_status(status: str) -> BrandTone:
    if status == "PASS":
        return BrandTone.SUCCESS
    if status == "WARNING":
        return BrandTone.WARNING
    return BrandTone.MUTATION


if __name__ == "__main__":
    main()
